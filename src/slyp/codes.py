from __future__ import annotations

import textwrap
import typing as t


class CodeDef:
    __slots__ = ("code", "message", "example", "hidden", "default_disabled")

    def __init__(
        self,
        code: str,
        message: str,
        example: str,
        hidden: bool = False,
        default_disabled: bool = False,
    ):
        self.code = code
        self.message = message
        self.example = textwrap.dedent(example).strip("\n")
        self.hidden = hidden
        self.default_disabled = default_disabled

    def __str__(self) -> str:
        return f"{self.message} ({self.code})"

    @property
    def category(self) -> str:
        return self.code[0]


ALL_CODES: list[CodeDef] = [
    # internal codes
    CodeDef("X001", "unparsable file", "foo(", hidden=True),
    CodeDef(
        "X002",
        "reached recursion limit during CST checks",
        "# see chardet",
        hidden=True,
    ),
    # errors & warnings, grouped by topic numerically
    # string concat
    CodeDef("E100", "unnecessary string concat", 'x = "foo " "bar"'),
    CodeDef(
        "W101",
        "unparenthesized multiline string concat in keyword arg",
        """
        foo(
            bar="alpha "
            "beta"
        )
        """,
    ),
    CodeDef(
        "W102",
        "unparenthesized multiline string concat in dict value",
        """
        {
            "foo": "alpha "
            "beta"
        }
        """,
    ),
    CodeDef(
        "W103",
        "unparenthesized multiline string concat in collection type",
        """
        x = (  # a tuple
            "alpha "
            "beta",
            "gamma"
        )
        x = {  # or a set
            "alpha "
            "beta",
            "gamma"
        }
        """,
    ),
    # returning known values
    CodeDef(
        "E110",
        "returning a variable checked as None, rather than returning None",
        """
        if x is None:
            return x  # should be `return None`
        """,
    ),
    # ast matching
    CodeDef(
        "W200",
        "two AST branches have identical contents",
        """
        if x is True:
            return y + 1
        else:
            # some comment
            return y + 1
        """,
    ),
    CodeDef(
        "W201",
        "two AST branches have identical trivial contents",
        """
        if x is True:
            return
        else:
            return
        """,
        default_disabled=True,
    ),
    CodeDef(
        "W202",
        "two non-adjacent AST branches have identical contents",
        """
        if x is True:
            return foo(bar())
        elif y is True:
            return 0
        elif z is True:
            return 1
        else:
            return foo(bar())
        """,
        default_disabled=True,
    ),
    CodeDef(
        "W203",
        "two non-adjacent AST branches have identical trivial contents",
        """
        if x is True:
            return None
        elif y is True:
            return 0
        elif z is True:
            return 1
        else:
            return None
        """,
        default_disabled=True,
    ),
]
CODE_MAP: dict[str, CodeDef] = {c.code: c for c in ALL_CODES}


def _generate_reference_raw() -> t.Iterator[str]:
    yield (
        """\
E is for "error" (you should probably change this)

W is for "warning" (you might want to change this)

Some warnings are disabled by default; enable them with `--enable`.
"""
    )

    for code in ALL_CODES:
        if code.hidden:
            continue
        yield ""
        yield f"### {code.code}"
        yield ""
        if code.default_disabled:
            yield "_disabled by default_"
            yield ""
        yield f"'{code.message}'"
        yield ""
        yield "```python"
        yield code.example
        yield "```"


def generate_reference() -> t.Iterator[str]:
    for s in _generate_reference_raw():
        if s == "":
            yield "\n"
        else:
            for sub in s.splitlines():
                yield sub + "\n"
