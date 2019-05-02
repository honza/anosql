import pytest

import anosql


@pytest.fixture
def sqlite(request):
    import sqlite3
    sqlconnection = sqlite3.connect(':memory:')

    def fin():
        "teardown"
        print("teardown")
        sqlconnection.close()

    request.addfinalizer(fin)

    return sqlconnection


def test_simple_query(sqlite):
    _test_create_insert = ("-- name: create-some-table#\n"
                           "-- testing insertion\n"
                           "CREATE TABLE foo (a, b, c);\n\n"
                           "-- name: insert-some-value!\n"
                           "INSERT INTO foo (a, b, c) VALUES (1, 2, 3);\n")

    q = anosql.from_str(_test_create_insert, "sqlite3")
    q.create_some_table(sqlite)
    q.insert_some_value(sqlite)


def test_auto_insert_query(sqlite):
    _test_create_insert = ("-- name: create-some-table#\n"
                           "-- testing insertion\n"
                           "CREATE TABLE foo (a, b, c);\n\n"
                           "-- name: insert-some-value<!\n"
                           "INSERT INTO foo (a, b, c) VALUES (1, 2, 3);\n")

    q = anosql.from_str(_test_create_insert, "sqlite3")
    q.create_some_table(sqlite)
    assert q.insert_some_value(sqlite) == 1
    assert q.insert_some_value(sqlite) == 2
    assert q.insert_some_value(sqlite) == 3


def test_parametrized_insert(sqlite):
    _test_create_insert = ("-- name: create-some-table#\n"
                           "-- testing insertion\n"
                           "CREATE TABLE foo (a, b, c);\n\n"
                           "-- name: insert-some-value!\n"
                           "INSERT INTO foo (a, b, c) VALUES (?, ?, ?);\n\n"
                           "-- name: get-all-values\n"
                           "SELECT * FROM foo;\n")

    q = anosql.from_str(_test_create_insert, "sqlite3")
    q.create_some_table(sqlite)
    q.insert_some_value(sqlite, 10, 11, 12)
    assert q.get_all_values(sqlite) == [(10, 11, 12)]


def test_parametrized_insert_named(sqlite):
    _test_create_insert = ("-- name: create-some-table#\n"
                           "-- testing insertion\n"
                           "CREATE TABLE foo (a, b, c);\n\n"
                           "-- name: insert-some-value!\n"
                           "INSERT INTO foo (a, b, c) VALUES (:a, :b, :c);\n\n"
                           "-- name: get-all-values\n"
                           "SELECT * FROM foo;\n")

    q = anosql.from_str(_test_create_insert, "sqlite3")
    q.create_some_table(sqlite)
    q.insert_some_value(sqlite, c=12, b=11, a=10)
    assert q.get_all_values(sqlite) == [(10, 11, 12)]


def test_simple_query_pg(postgresql):
    _queries = ("-- name: create-some-table#\n"
                "-- testing insertion\n"
                "CREATE TABLE foo (id serial primary key, a int, b int, c int);\n\n"
                "-- name: insert-some-value!\n"
                "INSERT INTO foo (a, b, c) VALUES (1, 2, 3);\n\n"
                "-- name: get-all-values\n"
                "SELECT a, b, c FROM foo;\n")

    q = anosql.from_str(_queries, "psycopg2")

    q.create_some_table(postgresql)
    q.insert_some_value(postgresql)

    assert q.get_all_values(postgresql) == [(1, 2, 3)]


def test_auto_insert_query_pg(postgresql):
    _queries = ("-- name: create-some-table#\n"
                "-- testing insertion\n"
                "CREATE TABLE foo (id serial primary key, a int, b int, c int);\n\n"
                "-- name: insert-some-value<!\n"
                "INSERT INTO foo (a, b, c) VALUES (1, 2, 3) returning id;\n\n"
                "-- name: get-all-values\n"
                "SELECT a, b, c FROM foo;\n")

    q = anosql.from_str(_queries, "psycopg2")

    q.create_some_table(postgresql)

    assert q.insert_some_value(postgresql) == 1
    assert q.insert_some_value(postgresql) == 2


def test_parameterized_insert_pg(postgresql):
    _queries = ("-- name: create-some-table#\n"
                "-- testing insertion\n"
                "CREATE TABLE foo (id serial primary key, a int, b int, c int);\n\n"
                "-- name: insert-some-value!\n"
                "INSERT INTO foo (a, b, c) VALUES (%s, %s, %s);\n\n"
                "-- name: get-all-values\n"
                "SELECT a, b, c FROM foo;\n")

    q = anosql.from_str(_queries, "psycopg2")

    q.create_some_table(postgresql)
    q.insert_some_value(postgresql, 1, 2, 3)

    assert q.get_all_values(postgresql) == [(1, 2, 3)]


def test_auto_parameterized_insert_query_pg(postgresql):
    _queries = ("-- name: create-some-table#\n"
                "-- testing insertion\n"
                "CREATE TABLE foo (id serial primary key, a int, b int, c int);\n\n"
                "-- name: insert-some-value<!\n"
                "INSERT INTO foo (a, b, c) VALUES (%s, %s, %s) returning id;\n\n"
                "-- name: get-all-values\n"
                "SELECT a, b, c FROM foo;\n")

    q = anosql.from_str(_queries, "psycopg2")

    q.create_some_table(postgresql)

    assert q.insert_some_value(postgresql, 1, 2, 3) == 1
    assert q.get_all_values(postgresql) == [(1, 2, 3)]

    assert q.insert_some_value(postgresql, 1, 2, 3) == 2


def test_parameterized_select_pg(postgresql):
    _queries = ("-- name: create-some-table#\n"
                "-- testing insertion\n"
                "CREATE TABLE foo (id serial primary key, a int, b int, c int);\n\n"
                "-- name: insert-some-value!\n"
                "INSERT INTO foo (a, b, c) VALUES (1, 2, 3)\n\n"
                "-- name: get-all-values\n"
                "SELECT a, b, c FROM foo WHERE a = %s;\n")

    q = anosql.from_str(_queries, "psycopg2")

    q.create_some_table(postgresql)
    q.insert_some_value(postgresql)

    assert q.get_all_values(postgresql, 1) == [(1, 2, 3)]


def test_parameterized_insert_named_pg(postgresql):
    _queries = ("-- name: create-some-table#\n"
                "-- testing insertion\n"
                "CREATE TABLE foo (id serial primary key, a int, b int, c int);\n\n"
                "-- name: insert-some-value!\n"
                "INSERT INTO foo (a, b, c) VALUES (%(a)s, %(b)s, %(c)s)\n\n"
                "-- name: get-all-values\n"
                "SELECT a, b, c FROM foo;\n")

    q = anosql.from_str(_queries, "psycopg2")

    q.create_some_table(postgresql)
    q.insert_some_value(postgresql, a=1, b=2, c=3)

    assert q.get_all_values(postgresql) == [(1, 2, 3)]


def test_parameterized_select_named_pg(postgresql):
    _queries = ("-- name: create-some-table#\n"
                "-- testing insertion\n"
                "CREATE TABLE foo (id serial primary key, a int, b int, c int);\n\n"
                "-- name: insert-some-value!\n"
                "INSERT INTO foo (a, b, c) VALUES (1, 2, 3)\n\n"
                "-- name: get-all-values\n"
                "SELECT a, b, c FROM foo WHERE a = %(a)s;\n")

    q = anosql.from_str(_queries, "psycopg2")

    q.create_some_table(postgresql)
    q.insert_some_value(postgresql)

    assert q.get_all_values(postgresql, a=1) == [(1, 2, 3)]


def test_without_trailing_semi_colon_pg():
    """Make sure keywords ending queries are recognized even without
    semi-colons.
    """
    _queries = ("-- name: get-by-a\n"
                "SELECT a, b, c FROM foo WHERE a = :a\n")
    q = anosql.from_str(_queries, "psycopg2")
    assert q.get_by_a.sql == "SELECT a, b, c FROM foo WHERE a = %(a)s"
