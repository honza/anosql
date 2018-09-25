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


@pytest.fixture
def postgres(request):
    import testing.postgresql
    import psycopg2

    postgresdb = testing.postgresql.Postgresql()
    sqlconnection = psycopg2.connect(**postgresdb.dsn())

    def fin():
        "teardown"
        print("teardown")
        sqlconnection.close()
        postgresdb.stop()

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
                           "INSERT INTO foo (a, b, c) VALUES (?, ?, ?);\n\n"
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


def test_simple_query_pg(postgres):
    _queries = ("-- name: create-some-table!\n"
                "-- testing insertion\n"
                "CREATE TABLE foo (id serial primary key, a int, b int, c int);\n\n"
                "-- name: insert-some-value<!\n"
                "INSERT INTO foo (a, b, c) VALUES (1, 2, 3);\n\n"
                "-- name: get-all-values\n"
                "SELECT a, b, c FROM foo;\n")

    q = anosql.load_queries_from_string("postgres", _queries)

    q.create_some_table(postgres)
    q.insert_some_value_auto(postgres)

    assert q.get_all_values(postgres) == [(1, 2, 3)]


def test_auto_insert_query_pg(postgres):
    _queries = ("-- name: create-some-table!\n"
                "-- testing insertion\n"
                "CREATE TABLE foo (id serial primary key, a int, b int, c int);\n\n"
                "-- name: insert-some-value<!\n"
                "INSERT INTO foo (a, b, c) VALUES (1, 2, 3);\n\n"
                "-- name: get-all-values\n"
                "SELECT a, b, c FROM foo;\n")

    q = anosql.load_queries_from_string("postgres", _queries)

    q.create_some_table(postgres)

    assert q.insert_some_value_auto(postgres) == 1
    assert q.insert_some_value_auto(postgres) == 2


def test_parameterized_insert_pg(postgres):
    _queries = ("-- name: create-some-table!\n"
                "-- testing insertion\n"
                "CREATE TABLE foo (id serial primary key, a int, b int, c int);\n\n"
                "-- name: insert-some-value!\n"
                "INSERT INTO foo (a, b, c) VALUES (%s, %s, %s);\n\n"
                "-- name: get-all-values\n"
                "SELECT a, b, c FROM foo;\n")

    q = anosql.load_queries_from_string("postgres", _queries)

    q.create_some_table(postgres)
    q.insert_some_value(postgres, 1, 2, 3)

    assert q.get_all_values(postgres) == [(1, 2, 3)]


def test_auto_parameterized_insert_query_pg(postgres):
    _queries = ("-- name: create-some-table!\n"
                "-- testing insertion\n"
                "CREATE TABLE foo (id serial primary key, a int, b int, c int);\n\n"
                "-- name: insert-some-value<!\n"
                "INSERT INTO foo (a, b, c) VALUES (%s, %s, %s);\n\n"
                "-- name: get-all-values\n"
                "SELECT a, b, c FROM foo;\n")

    q = anosql.load_queries_from_string("postgres", _queries)

    q.create_some_table(postgres)

    assert q.insert_some_value_auto(postgres, 1, 2, 3) == 1
    assert q.get_all_values(postgres) == [(1, 2, 3)]

    assert q.insert_some_value_auto(postgres, 1, 2, 3) == 2


def test_parameterized_select_pg(postgres):
    _queries = ("-- name: create-some-table!\n"
                "-- testing insertion\n"
                "CREATE TABLE foo (id serial primary key, a int, b int, c int);\n\n"
                "-- name: insert-some-value!\n"
                "INSERT INTO foo (a, b, c) VALUES (1, 2, 3)\n\n"
                "-- name: get-all-values\n"
                "SELECT a, b, c FROM foo WHERE a = %s;\n")

    q = anosql.load_queries_from_string("postgres", _queries)

    q.create_some_table(postgres)
    q.insert_some_value(postgres)

    assert q.get_all_values(postgres, 1) == [(1, 2, 3)]


def test_parameterized_insert_named_pg(postgres):
    _queries = ("-- name: create-some-table!\n"
                "-- testing insertion\n"
                "CREATE TABLE foo (id serial primary key, a int, b int, c int);\n\n"
                "-- name: insert-some-value!\n"
                "INSERT INTO foo (a, b, c) VALUES (%(a)s, %(b)s, %(c)s)\n\n"
                "-- name: get-all-values\n"
                "SELECT a, b, c FROM foo;\n")

    q = anosql.load_queries_from_string("postgres", _queries)

    q.create_some_table(postgres)
    q.insert_some_value(postgres, a=1, b=2, c=3)

    assert q.get_all_values(postgres) == [(1, 2, 3)]


def test_parameterized_select_named_pg(postgres):
    _queries = ("-- name: create-some-table!\n"
                "-- testing insertion\n"
                "CREATE TABLE foo (id serial primary key, a int, b int, c int);\n\n"
                "-- name: insert-some-value!\n"
                "INSERT INTO foo (a, b, c) VALUES (1, 2, 3)\n\n"
                "-- name: get-all-values\n"
                "SELECT a, b, c FROM foo WHERE a = %(a)s;\n")

    q = anosql.load_queries_from_string("postgres", _queries)

    q.create_some_table(postgres)
    q.insert_some_value(postgres)

    assert q.get_all_values(postgres, a=1) == [(1, 2, 3)]
