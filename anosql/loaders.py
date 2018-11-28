import re
from abc import ABCMeta, abstractmethod

from anosql.exceptions import SQLParseException


class SQLOperationType(object):
    SELECT = 1
    INSERT_UPDATE_DELETE = 2
    RETURNING = 3


class QueryLoader(object):
    __metaclass__ = ABCMeta

    op_types = SQLOperationType

    name_pattern = re.compile(r'\w+')
    doc_pattern = re.compile(r'\s*--\s*(.*)$')
    var_pattern = re.compile(
        r'(?P<dblquote>"[^"]+")|'
        r"(?P<quote>\'[^\']+\')|"
        r'(?P<lead>[^:]):(?P<var_name>[\w-]+)(?P<trail>[^:])'
    )

    def load(self, query_text):
        lines = query_text.strip().splitlines()
        name = lines[0].replace("-", "_")

        if name.endswith("<!"):
            op_type = self.op_types.RETURNING
            # FIXME: This is here for API compatibility only
            # The adding of "_auto" to the name of the methods obfuscates the connection between
            # the names a person puts in their "-- name: xxxx" definition in the sql. I don't think
            # it is necessary.
            name = name[:-2] + '_auto'
        elif name.endswith("!"):
            op_type = self.op_types.INSERT_UPDATE_DELETE
            name = name[:-1]
        else:
            op_type = self.op_types.SELECT

        use_col_description = False
        if name.startswith("$"):
            use_col_description = True
            name = name[1:]

        if not self.name_pattern.match(name):
            raise SQLParseException(
                'name must convert to valid python variable, got "{}".'.format(name)
            )

        docs = ''
        sql = ''
        for line in lines[1:]:
            match = self.doc_pattern.match(line)
            if match:
                docs += match.group(1) + "\n"
            else:
                sql += line + "\n"

        docs = docs.strip()
        sql = self.process_sql(name, op_type, sql.strip())

        fn = self.create_fn(name, op_type, sql, use_col_description)
        fn.__name__ = name
        fn.__docs__ = docs

        return name, fn

    @abstractmethod
    def process_sql(self, sql, op_type, name):
        pass

    @abstractmethod
    def create_fn(self, name, op_type, sql, use_col_description):
        pass


def replacer(match):
    gd = match.groupdict()
    if gd['dblquote'] is not None:
        return gd['dblquote']
    elif gd['quote'] is not None:
        return gd["quote"]
    else:
        return '{lead}%({var_name})s{trail}'.format(
            lead=gd['lead'],
            var_name=gd['var_name'],
            trail=gd['trail']
        )


class Psycopg2QueryLoader(QueryLoader):
    def process_sql(self, _name, op_type, sql):
        sql = self.var_pattern.sub(replacer, sql)

        # FIXME: This is here in order to not break API compatibility
        # This is problematic on a few levels.
        # 1. We're writing SQL for the user, which is mysterious
        # 2. There is nothing which guarantees that "id" is the proper name.
        # 3. In postgresql you can write returning statements which return multiple values
        #    and that should be the concern of the human being writing the sql, not this library.
        if op_type == self.op_types.RETURNING:
            sql = sql[:-1] if sql[-1] == ';' else sql
            sql += ' RETURNING id'

        return sql

    def create_fn(self, _name, op_type, sql, use_col_description):
        def fn(conn, *args, **kwargs):
            with conn.cursor() as cur:
                cur.execute(sql, kwargs if len(kwargs) > 0 else args)
                if op_type == self.op_types.INSERT_UPDATE_DELETE:
                    return None
                elif op_type == self.op_types.SELECT:
                    if use_col_description:
                        cols = [col[0] for col in cur.description]
                        return [dict(zip(cols, row)) for row in cur.fetchall()]
                    else:
                        return cur.fetchall()
                elif op_type == self.op_types.RETURNING:
                    pool = cur.fetchone()
                    return pool[0] if pool else None
                else:
                    raise RuntimeError('Unknown SQLOperationType: {}'.format(op_type))

        return fn


class SQLite3QueryLoader(QueryLoader):
    def process_sql(self, _name, _op_type, sql):
        return sql

    def create_fn(self, name, op_type, sql, use_col_description):
        def fn(conn, *args, **kwargs):
            results = None
            cur = conn.cursor()
            cur.execute(sql, kwargs if len(kwargs) > 0 else args)

            if op_type == self.op_types.SELECT:
                if use_col_description:
                    cols = [col[0] for col in cur.description]
                    results = [dict(zip(cols, row)) for row in cur.fetchall()]
                else:
                    results = cur.fetchall()
            elif op_type == self.op_types.RETURNING:
                results = cur.lastrowid

            cur.close()

            return results

        return fn


_LOADERS = {
    'postgres': lambda: Psycopg2QueryLoader(),
    'sqlite': lambda: SQLite3QueryLoader(),
}


def register_query_loader(db_type, loader):
    _LOADERS[db_type] = loader


def get_query_loader(db_type):
    try:
        loader = _LOADERS[db_type]
    except KeyError:
        raise ValueError('Encountered unregistered db_type: {}'.format(db_type))

    return loader() if callable(loader) else loader
