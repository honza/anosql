#########
Upgrading
#########

Upgrading from 0.x to 1.x
=========================

TODO topics to cover:

- No more ``$get-all-blogs`` style query names to indicate that the response should be a list of dictionary records with
column names as keys. Most database drivers have more complete features around controlling row output, and now we can let
you leverage those.

- Awareness of the ``_cursor`` context manager methods. Exposing users of ``anosql`` to the full api of their driver's
database cursor APIs.

- ``from_str`` and ``from_path`` instead of ``load_queries``, and ``load_queries_from_string``.

- Duck-typed ``driver_adapter`` over abstract base class approach of ``QueryLoader``. Providing a class which can act as
a database driver adapter is a simpler thing to make and means ``anosql`` no longer needs to expose the ``QueryLoader``
as part of it's API. This will also need an example of using ``register_query_loader`` vs ``register_driver_adapter``
This should also detail what the duck typed interface is, and how one needs to use ``@contextmanager``
