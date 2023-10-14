from __future__ import annotations

import sys
import typing as t

import libcst
import libcst.matchers

if sys.version_info >= (3, 10):
    from typing import TypeGuard
else:
    from typing_extensions import TypeGuard


class StrConcatErrorCollector(libcst.CSTVisitor):
    METADATA_DEPENDENCIES = (libcst.metadata.PositionProvider,)

    def __init__(self) -> None:
        self.errors: set[tuple[int, str]] = set()

    def visit_ConcatenatedString(self, node: libcst.ConcatenatedString) -> None:
        # check for 'unnecessary string concat' situations
        # e.g.
        #   x = "foo " "bar"
        #
        # these are easily introduced when strings change in length and `black` is run
        # also common when `black` runs for the first time on a project
        if libcst.matchers.matches(
            node.whitespace_between,
            libcst.matchers.SimpleWhitespace(
                value=libcst.matchers.MatchIfTrue(lambda x: "\n" not in x)
            ),
        ):
            lpos = self.get_metadata(libcst.metadata.PositionProvider, node.left).start
            self.errors.add((lpos.line, "E100"))

    def visit_Call(self, node: libcst.Call) -> None:
        # check for 'unparenthesized multiline string concat in keyword arg'
        # inside of function call sites
        #
        # the scenario here is that the string concat happens across multiple
        # lines, but without parenthesization
        # with a keyword argument getting the value, this is valid but results
        # in a string with different physical indentation levels in the file
        # e.g.
        #   foo(
        #       bar="alpha "
        #       "beta"
        #   )
        #
        # a classic case where this arises naturally is `help=...` for
        # argparse and click, where the help string is often slightly too long
        # for a single line, and easy to "break in two" without adding parens to
        # force the whole block to indent
        for arg in node.args:
            if not arg.keyword:
                continue

            value = arg.value
            if is_unparenthesized_multiline_concatenated_string(value):
                lpos = self.get_metadata(
                    libcst.metadata.PositionProvider, value.left
                ).start
                self.errors.add((lpos.line, "E101"))

    def visit_DictElement(self, node: libcst.DictElement) -> None:
        value = node.value
        if is_unparenthesized_multiline_concatenated_string(value):
            lpos = self.get_metadata(libcst.metadata.PositionProvider, value.left).start
            self.errors.add((lpos.line, "E102"))

    def visit_Tuple(self, node: libcst.Tuple) -> None:
        self._check_e103(node)

    def visit_List(self, node: libcst.List) -> None:
        self._check_e103(node)

    def visit_Set(self, node: libcst.Set) -> None:
        self._check_e103(node)

    def _check_e103(self, node: libcst.Tuple | libcst.List | libcst.Set) -> None:
        for element in node.elements:
            if libcst.matchers.matches(
                element,
                libcst.matchers.Element(
                    # mypy fails here, possibly the libcst types are incomplete (?)
                    value=unparenthesized_multiline_concatenated_string_matcher()  # type: ignore[arg-type]  # noqa: E501
                ),
            ):
                lpos = self.get_metadata(
                    libcst.metadata.PositionProvider,
                    t.cast(libcst.ConcatenatedString, element.value).left,
                ).start
                self.errors.add((lpos.line, "E103"))


def is_unparenthesized_multiline_concatenated_string(
    node: libcst.CSTNode,
) -> TypeGuard[libcst.ConcatenatedString]:
    return libcst.matchers.matches(
        node,
        unparenthesized_multiline_concatenated_string_matcher(),
    )


def unparenthesized_multiline_concatenated_string_matcher() -> (
    libcst.matchers.BaseMatcherNode
):
    return libcst.matchers.ConcatenatedString(
        whitespace_between=(
            libcst.matchers.SimpleWhitespace(
                value=libcst.matchers.MatchIfTrue(lambda x: "\n" in x)
            )
            | libcst.matchers.ParenthesizedWhitespace()
        ),
        # empty list means that there are no parens
        # because `lpar` and `rpar` are `Sequence[Paren]` types
        lpar=[],
        rpar=[],
    )
