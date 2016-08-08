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
    _test_create_insert = ("-- name: create-some-table\n"
                           "-- testing insertion\n"
                           "CREATE TABLE foo (a, b, c);\n\n"
                           "-- name: insert-some-value\n"
                           "INSERT INTO foo (a, b, c) VALUES (1, 2, 3);\n")

    q = anosql.load_queries_from_string("sqlite", _test_create_insert)
    q.create_some_table(sqlite)
    q.insert_some_value(sqlite)


def test_auto_insert_query(sqlite):
    _test_create_insert = ("-- name: create-some-table\n"
                           "-- testing insertion\n"
                           "CREATE TABLE foo (a, b, c);\n\n"
                           "-- name: insert-some-value<!\n"
                           "INSERT INTO foo (a, b, c) VALUES (1, 2, 3);\n")

    q = anosql.load_queries_from_string("sqlite", _test_create_insert)
    q.create_some_table(sqlite)
    assert q.insert_some_value_auto(sqlite) == 1
    assert q.insert_some_value_auto(sqlite) == 2
    assert q.insert_some_value_auto(sqlite) == 3


def test_parametrized_insert(sqlite):
    _test_create_insert = ("-- name: create-some-table\n"
                           "-- testing insertion\n"
                           "CREATE TABLE foo (a, b, c);\n\n"
                           "-- name: insert-some-value\n"
                           "INSERT INTO foo (a, b, c) VALUES (%s, %s, %s);\n\n"
                           "-- name: get-all-values\n"
                           "SELECT * FROM foo;\n")

    q = anosql.load_queries_from_string("sqlite", _test_create_insert)
    q.create_some_table(sqlite)
    q.insert_some_value(sqlite, 10, 11, 12)
    assert q.get_all_values(sqlite) == [(10, 11, 12)]


def test_parametrized_insert_named(sqlite):
    _test_create_insert = ("-- name: create-some-table\n"
                           "-- testing insertion\n"
                           "CREATE TABLE foo (a, b, c);\n\n"
                           "-- name: insert-some-value\n"
                           "INSERT INTO foo (a, b, c) VALUES (:a, :b, :c);\n\n"
                           "-- name: get-all-values\n"
                           "SELECT * FROM foo;\n")

    q = anosql.load_queries_from_string("sqlite", _test_create_insert)
    q.create_some_table(sqlite)
    q.insert_some_value(sqlite, c=12, b=11, a=10)
    assert q.get_all_values(sqlite) == [(10, 11, 12)]
