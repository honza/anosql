"""
anosql main module
"""

import os


class SQLLoadException(Exception):
    pass


class SQLParseException(Exception):
    pass


SELECT = 1
INSERT_UPDATE_DELETE = 2
AUTO_GEN = 3


class Queries(object):

    def __init__(self):
        self.available_queries = []

    def add_query(self, name, fn):
        setattr(self, name, fn)

        if name not in self.available_queries:
            self.available_queries.append(name)


def get_fn_name(line):
    line = line.replace('-', '_')
    return line[9:]


def parse_sql_entry(e):
    lines = e.split('\n')

    if not lines[0].startswith('-- name:'):
        raise SQLParseException()

    name = get_fn_name(lines[0])
    doc = None

    if '<!' in name:
        sql_type = AUTO_GEN
        name = name.replace('<!', '_auto')
    elif '!' in name:
        sql_type = INSERT_UPDATE_DELETE
        name = name.replace('!', '')
    else:
        sql_type = SELECT

    if lines[1].startswith('-- '):
        doc = lines[1][3:]

    if doc:
        query = lines[2:]
    else:
        query = lines[1:]

    query = ' '.join(query)

    if sql_type == AUTO_GEN:
        query += ' RETURNING id'

    def fn(conn, *args):
        results = None
        cur = conn.cursor()

        if sql_type == INSERT_UPDATE_DELETE:
            cur.execute(query, args)
            conn.commit()

        if sql_type == AUTO_GEN:
            cur.execute(query, args)
            results = cur.fetchone()[0]
            conn.commit()

        if sql_type == SELECT:
            if '%s' in query:
                cur.execute(query, args)
            else:
                cur.execute(query)
            results = cur.fetchall()

        cur.close()
        return results

    fn.__doc__ = doc
    fn.func_name = name

    return name, fn


def parse_queries_string(s):
    result = s.split('\n\n')
    result = map(parse_sql_entry, result)

    return result


def build_queries_object(queries):
    q = Queries()

    for name, fn in queries:
        q.add_query(name, fn)

    return q


def load_queries(filename):
    if not os.path.exists(filename):
        raise SQLLoadException('Could not read file', filename)

    f = open(filename).read()
    queries = parse_queries_string(f)
    return build_queries_object(queries)
