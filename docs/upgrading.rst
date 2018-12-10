#########
Upgrading
#########

Upgrading from 0.x to 1.x
=========================

Changed ``load_queries`` and ``load_queries_from_string``
---------------------------------------------------------

These methods were changed, mostly for brevity. To load ``anosql`` queries, you should now use
the ``anosql.from_str`` to load queries from a SQL string, and ``anosql.from_path`` to load queries
from a SQL file, or directory of SQL files.

Removed the ``$`` "record" operator
-----------------------------------

Because most database drivers have more efficient, robust, and featureful ways of controlling the
rows and records output, this feature was removed.

See:

* `sqlite.Row <https://docs.python.org/2/library/sqlite3.html#sqlite3.Row>`_
* `psycopg2 - Connection and Cursor subclasses <http://initd.org/psycopg/docs/extras.html#connection-and-cursor-subclasses>`_


SQLite example::

    conn = sqlite3.connect("...")
    conn.row_factory = sqlite3.Row
    actual = queries.get_all_users(conn)

    assert actual[0]["userid"] == 1
    assert actual[0]["username"] == "bobsmith"
    assert actual[0][2] == "Bob"
    assert actual[0]["lastname" == "Smith"

PostgreSQL example::

    with psycopg2.connect("...", cursor_factory=psycopg2.extras.RealDictCursor) as conn:
        actual = queries.get_all_users(conn)

    assert actual[0] == {
        "userid": 1,
        "username": "bobsmith",
        "firstname": "Bob",
        "lastname": "Smith",
    }

Driver Adapter classes instead of QueryLoader
---------------------------------------------

I'm not aware of anyone who actually has made or distributed an extension for ``anosql``, as it was
only available in its current form for a few weeks. So this notice is really just for completeness.

For ``0.3.x`` versions of ``anosql`` in order to add a new database extensions you had to build a
subclass of ``anosql.QueryLoader``. This base class is no longer available, and driver adapters no
longer have to extend from any class at all. They are duck-typed classes which are expected to
adhere to a standard interface. For more information about this see :ref:`Extending anosql <extending-anosql>`.

New Things
==========

Use the database driver ``cursor`` directly
-------------------------------------------

All the queries with a `SELECT` type have a duplicate method suffixed by `_cursor` which is a context manager to the database cursor. So `get_all_blogs(conn)` can also be used as:

::

    rows = queries.get_all_blogs(conn)
    # [(1, "My Blog", "yadayada"), ...]

    with queries.get_all_blogs_cursor(conn) as cur:
        # All the power of the underlying cursor object! Not limited to just a list of rows.
        for row in cur:
            print(row)


New operator types for runnings scripts ``#`` and bulk-inserts ``*!``
---------------------------------------------------------------------

See :ref:`Query Operations <query-operations>`
