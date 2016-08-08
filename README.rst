anosql
======

.. image:: https://badge.fury.io/py/anosql.svg
    :target: https://badge.fury.io/py/anosql

.. image:: http://readthedocs.org/projects/anosql/badge/?version=latest
    :target: http://anosql.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://travis-ci.org/honza/anosql.svg?branch=master
    :target: https://travis-ci.org/honza/anosql

A Python library for using SQL

*Warning: very alpha*

Inspired by the excellent `Yesql`_ library by Kris Jenkins.  In my mother
tongue, *ano* means *yes*.

Installation
------------

::

  $ pip install anosql

Usage
-----

Given a ``queries.sql`` file:

.. code-block:: sql

  -- name: get-all-greetings
  -- Get all the greetings in the database
  SELECT * FROM greetings;

We can issue SQL queries, like so:

.. code-block:: python

    import anosql
    import psycopg2
    import sqlite3

    # PostgreSQL
    conn = psycopg2.connect('...')
    queries = anosql.load_queries('postgres', 'queries.sql')

    # Or, Sqlite3...
    conn = sqlite3.connect('cool.db')
    queries = anosql.load_queries('sqlite', 'queries.sql')

    queries = queries.get_all_greetings(conn)
    # => [(1, 'Hi')]

    queries.get_all_greetings.__doc__
    # => Get all the greetings in the database

    queries.get_all_greetings.__query__
    # => SELECT * FROM greetings;

    queries.available_queries
    # => ['get_all_greetings']

Tests
-----

::

   $ pip install tox
   $ tox

Caveats
-------

Postgresql and sqlite only at the moment

License
-------

BSD, short and sweet

.. _Yesql: https://github.com/krisajenkins/yesql/
