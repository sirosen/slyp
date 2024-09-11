Linter Rules
============

.. generate-reference-insert-start

E is for "error" (you should probably change this)

W is for "warning" (you might want to change this)

Some warnings are disabled by default; enable them with ``--enable``.

E100
----

unnecessary string concat

.. code-block:: python

    x = "foo " "bar"

E101
----

unnecessary string concat with plus

.. code-block:: python

    x = "foo " + "bar"

W200
----

two AST branches have identical contents

.. code-block:: python

    if x is True:
        return y + 1
    else:
        # some comment
        return y + 1

W201
----

*disabled by default*

two AST branches have identical trivial contents

.. code-block:: python

    if x is True:
        return
    else:
        return

W202
----

*disabled by default*

two non-adjacent AST branches have identical contents

.. code-block:: python

    if x is True:
        return foo(bar())
    elif y is True:
        return 0
    elif z is True:
        return 1
    else:
        return foo(bar())

W203
----

*disabled by default*

two non-adjacent AST branches have identical trivial contents

.. code-block:: python

    if x is True:
        return None
    elif y is True:
        return 0
    elif z is True:
        return 1
    else:
        return None

.. generate-reference-insert-end
