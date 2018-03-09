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

Inspired by the excellent `Yesql`_ library by Kris Jenkins.  In my mother
tongue, *ano* means *yes*.

Installation
------------

::

  $ pip install anosql

Usage
-----

Basics
******

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

Parameters
**********

Often, you want to change parts of the query dynamically, particularly values in
the ``WHERE`` clause.  You can use parameters to do this:

.. code-block:: sql

  -- name: get-greetings-for-language-and-length
  -- Get all the greetings in the database
  SELECT * 
  FROM greetings
  WHERE lang = %s;

And they become positional parameters:

.. code-block:: python
  
  visitor_language = "en"
  queries.get_all_greetings(conn, visitor_language)



Named Parameters
****************

To make queries with many parameters more understandable and maintainable, you
can give the parameters names:

.. code-block:: sql

  -- name: get-greetings-for-language-and-length
  -- Get all the greetings in the database
  SELECT * 
  FROM greetings
  WHERE lang = :lang
  AND len(greeting) <= :length_limit;
  
If you were writing a Postgresql query, you could also format the parameters as
``%s(lang)`` and ``%s(length_limit)``.

Then, call your queries like you would any Python function with named
parameters:

.. code-block:: python
  
  visitor_language = "en"

  greetings_for_texting = queries.get_all_greetings(
                conn, lang=visitor_language, length_limit=140)


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
