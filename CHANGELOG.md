# Unreleased
<!-- changelog-unreleased-marker -->

# 0.4.0

- Various performance improvements, especially for fixing
- `slyp` will now cache results for files which pass all checks in
  `.slyp_cache`, thus avoiding rechecking files which pass and have
  not changed

  - this behavior can be disabled with `--no-cache`
  - the cache is maintained independently for each possible set of
    `--enable/--disable` options passed to `slyp`
  - projects which fully pass `slyp` checking should experience the greatest
    improvement -- as great as 50x faster on sizable production codebases with
    a populated cache

# 0.3.0

- Fix the handling of parenthesized lambdas in the fixer. The innermost
  parentheses arounda lambda are now preserved.
- Minor speed enhancements.
- Fix the handling of autofixing in certain expressions when there is no
  whitespace between a hard keyword and a parenthesis, inserting spaces when
  necessary.
- Fix unnecessarily parenthesized `with` and `from ... import ...` statements.
- Preserve parentheses immediately under unary operations, as they may aid
  readability.
- Remove W120. It is automatically fixed by the latest `black` versions.
- In restricted cases, the fixer will now automatically join implicitly
  concatenated strings when there is no newline. This autofix covers some cases
  of E100.

# 0.2.2

- Preserve the innermost parentheses when used inside of splat-argument
  expansion. e.g., `foo(*("a b".split()))` is NOT fixed to
  `foo(*"a b".split())`. This is semantically equivalent to the version with
  the parentheses removed, but not as obvious to readers.

# 0.2.1

- Fix unnecessary paren fixer aggressively fixing Comparison nodes. Add this to
  the set of nodes which retain their innermost parens.

# 0.2.0

- Improve handling on non-UTF8 files under `--use-git-ls`
- Helptext (`slyp --help`) now does not list all linting codes. Use
  `slyp --list` to view this data.
- Introduce autofixer behavior. Fixing is always run before linting, so that
  emitted lint errors are accurate to the fixed file.
  - The first autofixer has been added: remove unnecessary parentheses for
    expressions wrapped in multiple parentheses.

# 0.1.2

- Add `W120` for catching unparenthesized multiline annotations on parameters

# 0.1.1

- If CST traversal hits recursion depth, this is now reported as an internal
  error without aborting the entire run of `slyp`
- `W103` now ignores a multiline string join which is the only string inside
  of a container type.

# 0.1.0

- `--disable` and `--enable` now support the special string "all" to refer to
  all codes. Explicit enables and disables are given higher precedence than "all".
- Add `E110` for catching the return of a known-`None` variable immediately
  after testing it (prefer to return `None`, not the variable name)
- `--disable` and `--disable` now support categories, as in `--disable W`
  to disable all warnings.
- The `E101`, `E102`, and `E103` codes have each been downgraded to warnings
  (`W` category) but are still enabled by default
- The matching AST checker now considers the triviality and proximity of
  matching AST nodes. By default, only the check for non-trivial adjacent
  branches is enabled.
  - Add `W201`, `W202`, and `W203` to describe the disabled checks
  - Triviality is defined as a heuristic which captures simple expressions and
    statements (e.g. `return None` is a trivial statement)
- Add support for `--enable` to turn on disabled codes

# 0.0.3

- Add `--disable` for turning off specific codes
- Various minor speed improvements, resulting in ~5% faster runs on large
  codebases
- Invert verbosity control by removing `-q/--quiet` and adding `-v/--verbose`.
  Verbose output is now opt-in, not opt-out.

# 0.0.2

- Add pre-commit-hooks config, allowing use with pre-commit

# 0.0.1

- Initial release
