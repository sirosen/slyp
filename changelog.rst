Changelog
=========

Unreleased
----------

.. changelog-unreleased-marker

0.8.1
-----

- Bugfix: clear stale caches which could be incorrectly used in v0.8.0

0.8.0
-----

- Fix an ordering bug under libcst version 1.5.0 . New validation prevents the
  generation of invalid ``if`` nodes, which ``slyp`` was generating and then
  fixing. This applies to certain cases in which an ``if`` was not followed by
  a space, as in ``if(x): pass``. These cases may now require two runs to
  converge.
- Add fixer behavior to add a ``-> None`` return type annotation to
  ``__init__`` methods which have no return type annotation.

0.7.1
-----

- Fix a bug in which ``list(reversed(foo))`` was transformed to ``reversed(foo)``.
- Improve the handling of whitespace when wrapping concatenated strings

0.7.0
-----

- New autofixing behavior has been added, inspired by the rules of
  flake8-comprehensions. The following autofixing behaviors are newly
  added:

  - Calls to ``dict()``, ``list()``, and ``tuple()`` with no arguments are replaced
    with the relevant literals, ``{}``, ``[]``, and ``()``.
  - Calls to ``set()`` and ``list()`` on generator expressions are converted to set
    and list comprehensions.
  - Calls to ``dict()`` with keyword arguments are converted to dict literal
    syntax.
    e.g., ``dict(x=1)`` becomes ``{"x": 1}``
  - Calls to ``set()`` and ``frozenset()`` whose argument is a builtin which
    produces an iterable are unwrapped.
    e.g., ``set(list(foo()))`` becomes ``set(foo())``
  - Calls to ``list()`` whose argument is a builtin which produces a ``list`` are
    unwrapped.
    e.g., ``list(sorted(foo))`` becomes ``sorted(foo)``

.. note::

    The new transformation can be unsafe in certain rare cases. Specifically, the
    builtin names can be rebound to user-defined callables. This would
    potentially result in the fixer converting a meaningful call to these
    user-defined values.

    This can only occur if you rebind very well-known names,
    e.g., ``def dict(...): ...``

    Because there are no well-known cases in which such name shadowing is
    important or essential, this is not considered a bug. Just don't shadow
    these builtin names like that.
    You can always disable fixing with comments for certain lines.

0.6.1
-----

- Enable autofixing of some concatenated strings which combine f-strings with
  simple strings, as long as no extra escaping is needed
- Autofixing can be disabled with comments containing ``slyp: disable``,
  ``slyp: disable=format``, or ``fmt: off``. Inverse comments, ``slyp: enable`` and
  ``fmt: on`` can be used to re-enable autofixing.

0.6.0
-----

- Unexpected errors encountered when parsing files are now reported as failures, rather
  than causing ``slyp`` to abort
- Replace E110 with autofixer behavior, which rewrites the return of a known-``None``
  variable immediately after testing it to return ``None`` instead
- Replace W102 with autofixer behavior, which parenthesizes multiline
  concatenated strings in dict elements
- Replace W103 with autofixer behavior, which parenthesizes multiline
  concatenated strings in tuple, list, and set literals if there is more than
  one element
- Add the ``--only`` flag, enabling ``--only=lint`` or ``--only=fix`` to run only
  the linting or fixing
- Add basic support for reading data from stdin, in which case
  - ``--only`` must be used
  - if ``--only=fix``, then the resulting file is always written to stdout
- Implement an additional check for unnecessary string concatenation, E101

0.5.0
-----

- Replace the W101 lint with autofixer behavior, which will insert the
  necessary parentheses
- Improve the way that files are handled to read only once from disk per file
- ``slyp`` now processes files in parallel and produces its output at the end of
  its run (with some simple sorting)

0.4.1
-----

- Fix passing file caching to correctly record successes after a failure
- The cache implementation has been improved to cache by file contents rather
  than path, allowing duplicate files to share a cache entry

0.4.0
-----

- Various performance improvements, especially for fixing
- ``slyp`` will now cache results for files which pass all checks in
  ``.slyp_cache``, thus avoiding rechecking files which pass and have
  not changed

  - this behavior can be disabled with ``--no-cache``
  - the cache is maintained independently for each possible set of
    ``--enable/--disable`` options passed to ``slyp``
  - projects which fully pass ``slyp`` checking should experience the greatest
    improvement -- as great as 50x faster on sizable production codebases with
    a populated cache

0.3.0
-----

- Fix the handling of parenthesized lambdas in the fixer. The innermost
  parentheses arounda lambda are now preserved.
- Minor speed enhancements.
- Fix the handling of autofixing in certain expressions when there is no
  whitespace between a hard keyword and a parenthesis, inserting spaces when
  necessary.
- Fix unnecessarily parenthesized ``with`` and ``from ... import ...`` statements.
- Preserve parentheses immediately under unary operations, as they may aid
  readability.
- Remove W120. It is automatically fixed by the latest ``black`` versions.
- In restricted cases, the fixer will now automatically join implicitly
  concatenated strings when there is no newline. This autofix covers some cases
  of E100.

0.2.2
-----

- Preserve the innermost parentheses when used inside of splat-argument
  expansion. e.g., ``foo(*("a b".split()))`` is NOT fixed to
  ``foo(*"a b".split())``. This is semantically equivalent to the version with
  the parentheses removed, but not as obvious to readers.

0.2.1
-----

- Fix unnecessary paren fixer aggressively fixing Comparison nodes. Add this to
  the set of nodes which retain their innermost parens.

0.2.0
-----

- Improve handling on non-UTF8 files under ``--use-git-ls``
- Helptext (``slyp --help``) now does not list all linting codes. Use
  ``slyp --list`` to view this data.
- Introduce autofixer behavior. Fixing is always run before linting, so that
  emitted lint errors are accurate to the fixed file.

  - The first autofixer has been added: remove unnecessary parentheses for
    expressions wrapped in multiple parentheses.

0.1.2
-----

- Add ``W120`` for catching unparenthesized multiline annotations on parameters

0.1.1
-----

- If CST traversal hits recursion depth, this is now reported as an internal
  error without aborting the entire run of ``slyp``
- ``W103`` now ignores a multiline string join which is the only string inside
  of a container type.

0.1.0
-----

- ``--disable`` and ``--enable`` now support the special string "all" to refer to
  all codes. Explicit enables and disables are given higher precedence than "all".
- Add ``E110`` for catching the return of a known-``None`` variable immediately
  after testing it (prefer to return ``None``, not the variable name)
- ``--disable`` and ``--disable`` now support categories, as in ``--disable W``
  to disable all warnings.
- The ``E101``, ``E102``, and ``E103`` codes have each been downgraded to warnings
  (``W`` category) but are still enabled by default
- The matching AST checker now considers the triviality and proximity of
  matching AST nodes. By default, only the check for non-trivial adjacent
  branches is enabled.

  - Add ``W201``, ``W202``, and ``W203`` to describe the disabled checks
  - Triviality is defined as a heuristic which captures simple expressions and
    statements (e.g. ``return None`` is a trivial statement)

- Add support for ``--enable`` to turn on disabled codes

0.0.3
-----

- Add ``--disable`` for turning off specific codes
- Various minor speed improvements, resulting in ~5% faster runs on large
  codebases
- Invert verbosity control by removing ``-q/--quiet`` and adding ``-v/--verbose``.
  Verbose output is now opt-in, not opt-out.

0.0.2
-----

- Add pre-commit-hooks config, allowing use with pre-commit

0.0.1
-----

- Initial release
