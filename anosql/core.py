"""
anosql main module
"""

import os
from functools import partial
import re


class SQLLoadException(Exception):
    pass


class SQLParseException(Exception):
    pass


SELECT = 1
INSERT_UPDATE_DELETE = 2
AUTO_GEN = 3


class Queries(object):

    def __init__(self, queries=list()):
        self.available_queries = []

        for name, fn in queries:
            self.add_query(name, fn)

    def __repr__(self):
        return "anosql.Queries(" + self.available_queries.__repr__() + ")"

    def add_query(self, name, fn):
        setattr(self, name, fn)

        if name not in self.available_queries:
            self.available_queries.append(name)


def parse_sql_entry(db_type, e):
    assert db_type in [ 'sqlite', 'postgres' ]

    lines = e.splitlines()

    # name of query
    is_name = re.compile(r'\s*--\s+name\s*:\s*(\S+)').match
    has_name = is_name(lines[0])
    if not has_name:
        raise SQLParseException('Query does not start with "-- name:".')

    name = has_name.group(1).replace('-', '_')

    # type of query
    if '<!' in name:
        sql_type = AUTO_GEN
        name = name.replace('<!', '_auto')
    elif '!' in name:
        sql_type = INSERT_UPDATE_DELETE
        name = name.replace('!', '')
    else:
        sql_type = SELECT

    # documentation are comment lines after the initial name
    is_doc = re.compile(r'\s*--\s(.*)').match
    doc = ''
    for i in range(1, len(lines)):
        has_doc = is_doc(lines[i])
        if has_doc:
            doc += has_doc.group(1) + '\n'
        else:
            break

    # what remains is the query
    query = ' '.join(lines[i:])

    if query == '':
        return None, None

    # ??? this is rather ad-hoc:-(
    if sql_type == AUTO_GEN and db_type == 'postgres':
        query += ' RETURNING id'

    # ??? postgres psycopg2 supports %s...
    if db_type == 'sqlite':
        query = query.replace('%s', '?')
    elif db_type == 'postgres':
        query = re.sub(r'[^:]:([a-zA-Z_-]+)', r'%(\1)s', query)

    # dynamically create the "name" function
    def fn(conn, *args, **kwargs):
        # ???
        #if db_type == 'sqlite':
        #    assert len(kwargs) == 0
        results = None
        cur = conn.cursor()
        cur.execute(query, kwargs if len(kwargs) > 0 else args)

        if sql_type == SELECT:
            results = cur.fetchall()
        elif sql_type == AUTO_GEN:
            if db_type == 'postgres':
                results = cur.fetchone()[0]
            elif db_type == 'sqlite':
                results = cur.lastrowid

        cur.close()
        return results

    fn.__doc__ = doc
    fn.__query__ = query
    fn.func_name = name

    return name, fn


def parse_queries_string(db_type, s):
    return [parse_sql_entry(db_type, expression)
            for expression in re.split(r'([ \t]*\r|[ \t]*\n|[ \t]*\r\n){2,}', s)[::2]]


def load_queries(db_type, filename):
    if not os.path.exists(filename):
        raise SQLLoadException('Could not read file', filename)

    with open(filename) as queries_file:
        f = queries_file.read()

    queries = parse_queries_string(db_type, f)
    return Queries(queries)


def load_queries_from_string(db_type, string):
    queries = parse_queries_string(db_type, string)
    return Queries(queries)
