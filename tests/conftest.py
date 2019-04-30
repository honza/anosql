import csv
import os
import sqlite3

import pytest

BLOGDB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blogdb")
USERS_DATA_PATH = os.path.join(BLOGDB_PATH, "data", "users_data.csv")
BLOGS_DATA_PATH = os.path.join(BLOGDB_PATH, "data", "blogs_data.csv")


def populate_sqlite3_db(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executescript(
        """
            create table users (
                userid integer not null primary key,
                username text not null,
                firstname integer not null,
                lastname text not null
            );

            create table blogs (
                blogid integer not null primary key,
                userid integer not null,
                title text not null,
                content text not null,
                published date not null default CURRENT_DATE,
                foreign key(userid) references users(userid)
            );
            """
    )

    with open(USERS_DATA_PATH) as fp:
        users = list(csv.reader(fp))
        cur.executemany(
            """
               insert into users (
                    username,
                    firstname,
                    lastname
               ) values (?, ?, ?);""",
            users,
        )
    with open(BLOGS_DATA_PATH) as fp:
        blogs = list(csv.reader(fp))
        cur.executemany(
            """
                insert into blogs (
                    userid,
                    title,
                    content,
                    published
                ) values (?, ?, ?, ?);""",
            blogs,
        )

    conn.commit()
    conn.close()


@pytest.fixture()
def sqlite3_db_path(tmpdir):
    db_path = os.path.join(tmpdir.strpath, "blogdb.db")
    populate_sqlite3_db(db_path)
    return db_path


@pytest.fixture()
def sqlite3_conn(sqlite3_db_path):
    conn = sqlite3.connect(sqlite3_db_path)
    yield conn
    conn.close()


@pytest.fixture
def pg_conn(postgresql):
    with postgresql:
        # Loads data from blogdb fixture data
        with postgresql.cursor() as cur:
            cur.execute(
                """
                create table users (
                    userid serial not null primary key,
                    username varchar(32) not null,
                    firstname varchar(255) not null,
                    lastname varchar(255) not null
                );"""
            )
            cur.execute(
                """
                create table blogs (
                    blogid serial not null primary key,
                    userid integer not null references users(userid),
                    title varchar(255) not null,
                    content text not null,
                    published date not null default CURRENT_DATE
                );"""
            )

        with postgresql.cursor() as cur:
            with open(USERS_DATA_PATH) as fp:
                cur.copy_from(fp, "users", sep=",", columns=["username", "firstname", "lastname"])
            with open(BLOGS_DATA_PATH) as fp:
                cur.copy_from(
                    fp, "blogs", sep=",", columns=["userid", "title", "content", "published"]
                )

    return postgresql


@pytest.fixture()
def pg_dsn(pg_conn):
    p = pg_conn.get_dsn_parameters()
    return "postgres://{user}@{host}:{port}/{dbname}".format(**p)
