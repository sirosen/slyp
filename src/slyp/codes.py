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
    ) -> None:
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
    CodeDef("E101", "unnecessary string concat with plus", 'x = "foo " + "bar"'),
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

Some warnings are disabled by default; enable them with ``--enable``.
"""
    )

    for code in ALL_CODES:
        if code.hidden:
            continue
        yield ""
        yield f"{code.code}"
        yield f"{'-' * len(code.code)}"
        yield ""
        if code.default_disabled:
            yield "*disabled by default*"
            yield ""
        yield f"{code.message}"
        yield ""
        yield ".. code-block:: python"
        yield ""
        yield textwrap.indent(code.example, "    ")


def generate_reference() -> t.Iterator[str]:
    for s in _generate_reference_raw():
        if s == "":
            yield "\n"
        else:
            for sub in s.splitlines():
                yield sub + "\n"
