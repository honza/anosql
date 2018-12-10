import os

from anosql.adapters.psycopg2 import PsycoPG2Adapter
from anosql.adapters.sqlite3 import SQLite3DriverAdapter
from anosql.exceptions import SQLLoadException, SQLParseException
from anosql.patterns import (
    query_name_definition_pattern,
    empty_pattern,
    doc_comment_pattern,
    valid_query_name_pattern,
)


_ADAPTERS = {
    "psycopg2": PsycoPG2Adapter,
    "sqlite3": SQLite3DriverAdapter,
}


def register_driver_adapter(driver_name, driver_adapter):
    """Registers custom driver adapter classes to extend ``anosql`` to to handle additional drivers.

    For details on how to create a new driver adapter see :ref:`driver-adapters` documentation.

    Args:
        driver_name (str): The driver type name.
        driver_adapter (callable): Either n class or function which creates an instance of a
                                   driver adapter.

    Returns:
        None

    Examples:
        To register a new loader::

            class MyDbAdapter():
                def process_sql(self, name, op_type, sql):
                    pass

                def select(self, conn, sql, parameters):
                    pass

                @contextmanager
                def select_cursor(self, conn, sql, parameters):
                    pass

                def insert_update_delete(self, conn, sql, parameters):
                    pass

                def insert_update_delete_many(self, conn, sql, parameters):
                    pass

                def insert_returning(self, conn, sql, parameters):
                    pass

                def execute_script(self, conn, sql):
                    pass


            anosql.register_driver_adapter("mydb", MyDbAdapter)

        If your adapter constructor takes arguments you can register a function which can build
        your adapter instance::

            def adapter_factory():
                return MyDbAdapter("foo", 42)

            anosql.register_driver_adapter("mydb", adapter_factory)

    """
    _ADAPTERS[driver_name] = driver_adapter


def get_driver_adapter(driver_name):
    """Get the driver adapter instance registered by the ``driver_name``.

    Args:
        driver_name (str): The database driver name.

    Returns:
        object: A driver adapter class.
    """
    try:
        driver_adapter = _ADAPTERS[driver_name]
    except KeyError:
        raise ValueError("Encountered unregistered driver_name: {}".format(driver_name))

    return driver_adapter()


class SQLOperationType(object):
    """Enumeration (kind of) of anosql operation types
    """
    INSERT_RETURNING = 0
    INSERT_UPDATE_DELETE = 1
    INSERT_UPDATE_DELETE_MANY = 2
    SCRIPT = 3
    SELECT = 4


class Queries:
    """Container object with dynamic methods built from SQL queries.

    The ``-- name`` definition comments in the SQL content determine what the dynamic
    methods of this class will be named.

    @DynamicAttrs
    """

    def __init__(self, queries=None):
        """Queries constructor.

        Args:
            queries (list(tuple)):
        """
        if queries is None:
            queries = []
        self._available_queries = set()

        for query_name, fn in queries:
            self.add_query(query_name, fn)

    @property
    def available_queries(self):
        """Returns listing of all the available query methods loaded in this class.

        Returns:
            list(str): List of dot-separated method accessor names.
        """
        return sorted(self._available_queries)

    def __repr__(self):
        return "Queries(" + self.available_queries.__repr__() + ")"

    def add_query(self, query_name, fn):
        """Adds a new dynamic method to this class.

        Args:
            query_name (str): The method name as found in the SQL content.
            fn (function): The loaded query function.

        Returns:

        """
        setattr(self, query_name, fn)
        self._available_queries.add(query_name)

    def add_child_queries(self, child_name, child_queries):
        """Adds a Queries object as a property.

        Args:
            child_name (str): The property name to group the child queries under.
            child_queries (Queries): Queries instance to add as sub-queries.

        Returns:
            None

        """
        setattr(self, child_name, child_queries)
        for child_query_name in child_queries.available_queries:
            self._available_queries.add("{}.{}".format(child_name, child_query_name))


def _create_fns(query_name, docs, op_type, sql, driver_adapter):
    def fn(conn, *args, **kwargs):
        parameters = kwargs if len(kwargs) > 0 else args
        if op_type == SQLOperationType.INSERT_RETURNING:
            return driver_adapter.insert_returning(conn, query_name, sql, parameters)
        elif op_type == SQLOperationType.INSERT_UPDATE_DELETE:
            return driver_adapter.insert_update_delete(conn, query_name, sql, parameters)
        elif op_type == SQLOperationType.INSERT_UPDATE_DELETE_MANY:
            return driver_adapter.insert_update_delete_many(conn, query_name, sql, *parameters)
        elif op_type == SQLOperationType.SCRIPT:
            return driver_adapter.execute_script(conn, sql)
        elif op_type == SQLOperationType.SELECT:
            return driver_adapter.select(conn, query_name, sql, parameters)
        else:
            raise ValueError("Unknown op_type: {}".format(op_type))

    fn.__name__ = query_name
    fn.__doc__ = docs
    fn.sql = sql

    ctx_mgr_method_name = "{}_cursor".format(query_name)

    def ctx_mgr(conn, *args, **kwargs):
        parameters = kwargs if len(kwargs) > 0 else args
        return driver_adapter.select_cursor(conn, query_name, sql, parameters)

    ctx_mgr.__name__ = ctx_mgr_method_name
    ctx_mgr.__doc__ = docs
    ctx_mgr.sql = sql

    if op_type == SQLOperationType.SELECT:
        return [(query_name, fn), (ctx_mgr_method_name, ctx_mgr)]

    return [(query_name, fn)]


def load_methods(sql_text, driver_adapter):
    lines = sql_text.strip().splitlines()
    query_name = lines[0].replace("-", "_")

    if query_name.endswith("<!"):
        op_type = SQLOperationType.INSERT_RETURNING
        query_name = query_name[:-2]
    elif query_name.endswith("*!"):
        op_type = SQLOperationType.INSERT_UPDATE_DELETE_MANY
        query_name = query_name[:-2]
    elif query_name.endswith("!"):
        op_type = SQLOperationType.INSERT_UPDATE_DELETE
        query_name = query_name[:-1]
    elif query_name.endswith("#"):
        op_type = SQLOperationType.SCRIPT
        query_name = query_name[:-1]
    else:
        op_type = SQLOperationType.SELECT

    if not valid_query_name_pattern.match(query_name):
        raise SQLParseException(
            'name must convert to valid python variable, got "{}".'.format(query_name)
        )

    docs = ""
    sql = ""
    for line in lines[1:]:
        match = doc_comment_pattern.match(line)
        if match:
            docs += match.group(1) + "\n"
        else:
            sql += line + "\n"

    docs = docs.strip()
    sql = driver_adapter.process_sql(query_name, op_type, sql.strip())

    return _create_fns(query_name, docs, op_type, sql, driver_adapter)


def load_queries_from_sql(sql, driver_adapter):
    queries = []
    for query_text in query_name_definition_pattern.split(sql):
        if not empty_pattern.match(query_text):
            for method_pair in load_methods(query_text, driver_adapter):
                queries.append(method_pair)
    return queries


def load_queries_from_file(file_path, driver_adapter):
    with open(file_path) as fp:
        return load_queries_from_sql(fp.read(), driver_adapter)


def load_queries_from_dir_path(dir_path, query_loader):
    if not os.path.isdir(dir_path):
        raise ValueError("The path {} must be a directory".format(dir_path))

    def _recurse_load_queries(path):
        queries = Queries()
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path) and not item.endswith(".sql"):
                continue
            elif os.path.isfile(item_path) and item.endswith(".sql"):
                for name, fn in load_queries_from_file(item_path, query_loader):
                    queries.add_query(name, fn)
            elif os.path.isdir(item_path):
                child_queries = _recurse_load_queries(item_path)
                queries.add_child_queries(item, child_queries)
            else:
                # This should be practically unreachable.
                raise SQLLoadException(
                    "The path must be a directory or file, got {}".format(item_path)
                )
        return queries

    return _recurse_load_queries(dir_path)


def from_str(sql, driver_name):
    """Load queries from a SQL string.

    Args:
        sql (str) A string containing SQL statements and anosql name:
        driver_name (str): The database driver to use to load and execute queries.

    Returns:
        Queries

    Example:
        Loading queries from a SQL string::

            import sqlite3
            import anosql

            sql_text = \"""
            -- name: get-all-greetings
            -- Get all the greetings in the database
            select * from greetings;

            -- name: get-users-by-username
            -- Get all the users from the database,
            -- and return it as a dict
            select * from users where username =:username;
            \"""

            queries = anosql.from_str(sql_text, db_driver="sqlite3")
            queries.get_all_greetings(conn)
            queries.get_users_by_username(conn, username="willvaughn")

    """
    driver_adapter = get_driver_adapter(driver_name)
    return Queries(load_queries_from_sql(sql, driver_adapter))


def from_path(sql_path, driver_name):
    """Load queries from a sql file, or a directory of sql files.

    Args:
        sql_path (str): Path to a ``.sql`` file or directory containing ``.sql`` files.
        driver_name (str): The database driver to use to load and execute queries.

    Returns:
        Queries

    Example:
        Loading queries paths::

            import sqlite3
            import anosql

            queries = anosql.from_path("./greetings.sql", driver_name="sqlite3")
            queries2 = anosql.from_path("./sql_dir", driver_name="sqlite3")

    """
    if not os.path.exists(sql_path):
        raise SQLLoadException('File does not exist: {}.'.format(sql_path), sql_path)

    driver_adapter = get_driver_adapter(driver_name)

    if os.path.isdir(sql_path):
        return load_queries_from_dir_path(sql_path, driver_adapter)
    elif os.path.isfile(sql_path):
        return Queries(load_queries_from_file(sql_path, driver_adapter))
    else:
        raise SQLLoadException(
            'The sql_path must be a directory or file, got {}'.format(sql_path),
            sql_path
        )
