Fixer Rules
===========

Fixer rules do not have codes, and cannot be individually enabled and disabled.

Instead, use ``# fmt: off`` comments to disable all formatting for a block of
code.

Remove Unnecessary Parentheses
------------------------------

Parentheses which can safely be removed from expressions are:

.. code-block:: diff

    -x = (foo.bar)
    +x = foo.bar

Parenthesize Multiline str-concat in List Context
-------------------------------------------------

In a listing context, such as an argument list or collection literal, multiline
string concatenation is parenthesized and indented:

.. code-block:: diff

     x = foo(
        a=1,
    -   b="abcdefg "
    -   "hijklmnop"
    +   b=(
    +       "abcdefg "
    +       "hijklmnop"
    +   )
     )

Convert Collection Builtin Calls to Literals
--------------------------------------------

.. warning::

    This transformation can be harmful if you rebind builtin names like ``dict``.

Builtins like ``dict``, ``list``, and ``set`` are converted to their relevant
literal types.

.. code-block:: diff

    -x = dict(
    -    a=1,
    -    b="foo"
    -)
    +x = {
    +    "a": 1,
    +    "b": "foo"
    +}


Set and List Calls Remove Unnecessary Iterable Builtins
-------------------------------------------------------

.. warning::

    This transformation can be harmful if you rebind builtin names like ``sorted``.

If ``set()`` is used on a known builtin which transforms an iterator, the
transform can typically be removed. And if ``list`` is used on a known ordered
iterator, then the same holds and on of the wrapping layers can be removed.

.. code-block:: diff

    -x = set(list(y))
    +x = set(y)
    -z = list(sorted(foo))
    +z = sorted(foo)


Prefer ``return None`` after ``None`` Check
-------------------------------------------

After checking ``if x is None``, do not return ``x``.

.. code-block:: diff

    if x is None:
    -    return x
    +    return None


Auto-concat Inline Strings
--------------------------

.. note::

    This situation is a common artifact from running ``black`` on a codebase.

When strings are implicitly concatenated on a single line, join them together
if possible.

.. code-block:: diff

    -x = "foo " "bar"
    +x = "foo bar"
    -y = f"{item1} " f"{item2}"
    +y = f"{item1} {item2}"


Always annotate ``__init__` with ``-> None``
--------------------------------------------

.. note::

    An unannotated initializer with no args is treated by type checkers as an
    unannotated function. i.e. ``def __init__(self): ...`` is not annotated.
    But adding a ``-> None`` annotation makes it into an annotated function,
    and can change checker behaviors.

    By contrast, ``def __init__(self, x: int): ...`` is treated as annotated,
    and the ``-> None`` is not needed to mark it as annotated.

    This results in discrepancies between code with an without the return type
    annotation.

When defining initializers, always declare the return type as ``None``.

.. code-block:: diff

     class A:
    -    def __init__(self):
    +    def __init__(self) -> None:
             self.x = 1
