"""
anosql main module
"""

import os
import re

from anosql.loaders import get_query_loader
from anosql.exceptions import SQLLoadException

namedef_pattern = re.compile(r'--\s*name\s*:\s*')
empty_pattern = re.compile(r'^\s*$')


class Queries(object):
    """Stores SQL Queries as attributes.
    @DynamicAttrs
    """

    def __init__(self, queries=None):
        if queries is None:
            queries = []
        self._available_queries = set()

        for name, fn in queries:
            self.add_query(name, fn)

    @property
    def available_queries(self):
        return sorted(self._available_queries)

    def __repr__(self):
        return 'Queries(' + self.available_queries.__repr__() + ')'

    def add_query(self, name, fn):
        setattr(self, name, fn)
        self._available_queries.add(name)

    def add_child_queries(self, name, child_queries):
        setattr(self, name, child_queries)
        for child_name in child_queries.available_queries:
            self._available_queries.add('{}.{}'.format(name, child_name))


def load_queries_from_sql(sql, query_loader):
    queries = []
    for query_text in namedef_pattern.split(sql):
        if not empty_pattern.match(query_text):
            queries.append(query_loader.load(query_text))
    return queries


def load_queries_from_file(file_path, query_loader):
    with open(file_path) as fp:
        return load_queries_from_sql(fp.read(), query_loader)


def load_queries_from_dir_path(dir_path, query_loader):
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
                raise RuntimeError(item_path)
        return queries

    return _recurse_load_queries(dir_path)


def load_queries_from_string(db_type, sql):
    query_loader = get_query_loader(db_type)
    return Queries(load_queries_from_sql(sql, query_loader))


def load_queries(db_type, path):
    if not os.path.exists(path):
        raise SQLLoadException('File does not exist: {}.'.format(path), path)

    query_loader = get_query_loader(db_type)

    if os.path.isdir(path):
        return load_queries_from_dir_path(path, query_loader)
    elif os.path.isfile(path):
        return Queries(load_queries_from_file(path, query_loader))
    else:
        raise SQLLoadException('Could not read file: {}'.format(path), path)
