from __future__ import annotations

import libcst
import libcst.matchers

from ._base import ErrorCollectingVisitor

UNPARENTHESIZED_MULTILINE_CONCATENATED_STRING_MATCHER = libcst.matchers.ConcatenatedString(  # noqa: E501
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

# SimpleWhitespace defines whitespace as seen between tokens in most contexts
# it can contain newlines *if* there is a preceding backslash escape
SIMPLE_WHITESPACE_NO_NEWLINE_MATCHER = libcst.matchers.SimpleWhitespace(
    value=libcst.matchers.MatchIfTrue(lambda x: "\n" not in x)
)

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
W101_KWARG_MATCHER = libcst.matchers.Arg(
    keyword=libcst.matchers.Name(),
    value=UNPARENTHESIZED_MULTILINE_CONCATENATED_STRING_MATCHER,
)

# check for 'unparenthesized multiline string concat in container'
#
# this case is multiline str concat inside of a container type, containing other
# elements
#
# the main scenario is "accidental multiline string", where a collection contains
# string literals, but is missing one comma
#
#   x = [
#       "foo "
#       "bar",
#       "baz",
#   ]
#
# however, a similar argument applies to any mixed iterable, e.g.
#
#   x = (
#       "foo "
#       "bar",
#       baz(),
#   ]
W103_ELEMENT_MATCHER = libcst.matchers.Element(
    value=UNPARENTHESIZED_MULTILINE_CONCATENATED_STRING_MATCHER
)

# this allows us to do faster matching for W103 by checking the whole list with
# a single matcher conditional
W103_IN_ELEMENT_LIST_MATCHER = libcst.matchers.OneOf(
    [
        libcst.matchers.AtLeastN(n=1),
        W103_ELEMENT_MATCHER,
        libcst.matchers.ZeroOrMore(),
    ],
    [
        libcst.matchers.ZeroOrMore(),
        W103_ELEMENT_MATCHER,
        libcst.matchers.AtLeastN(n=1),
    ],
)


class StrConcatErrorCollector(ErrorCollectingVisitor):
    METADATA_DEPENDENCIES = (libcst.metadata.PositionProvider,)

    def visit_ConcatenatedString(self, node: libcst.ConcatenatedString) -> None:
        # check for 'unnecessary string concat' situations
        # e.g.
        #   x = "foo " "bar"
        #
        # these are easily introduced when strings change in length and `black` is run
        # also common when `black` runs for the first time on a project
        if libcst.matchers.matches(
            node.whitespace_between, SIMPLE_WHITESPACE_NO_NEWLINE_MATCHER
        ):
            lpos = self.get_metadata(libcst.metadata.PositionProvider, node.left).start
            self.errors.add((lpos.line, self.filename, "E100"))

    def visit_Arg(self, node: libcst.Arg) -> None:
        if libcst.matchers.matches(node, W101_KWARG_MATCHER):
            lpos = self.get_metadata(
                libcst.metadata.PositionProvider,
                node.value.left,  # type: ignore[attr-defined]
            ).start
            self.errors.add((lpos.line, self.filename, "W101"))

    def visit_DictElement(self, node: libcst.DictElement) -> None:
        if libcst.matchers.matches(
            node.value,
            UNPARENTHESIZED_MULTILINE_CONCATENATED_STRING_MATCHER,
        ):
            lpos = self.get_metadata(
                libcst.metadata.PositionProvider,
                node.value.left,  # type: ignore[attr-defined]
            ).start
            self.errors.add((lpos.line, self.filename, "W102"))

    def visit_Tuple(self, node: libcst.Tuple) -> None:
        if libcst.matchers.matches(
            node,
            libcst.matchers.Tuple(
                elements=W103_IN_ELEMENT_LIST_MATCHER  # type: ignore[arg-type]
            ),
        ):
            self._collect_w103(node)

    def visit_List(self, node: libcst.List) -> None:
        if libcst.matchers.matches(
            node,
            libcst.matchers.List(
                elements=W103_IN_ELEMENT_LIST_MATCHER  # type: ignore[arg-type]
            ),
        ):
            self._collect_w103(node)

    def visit_Set(self, node: libcst.Set) -> None:
        if libcst.matchers.matches(
            node,
            libcst.matchers.Set(
                elements=W103_IN_ELEMENT_LIST_MATCHER  # type: ignore[arg-type]
            ),
        ):
            self._collect_w103(node)

    def _collect_w103(self, node: libcst.Tuple | libcst.List | libcst.Set) -> None:
        for element in node.elements:
            if libcst.matchers.matches(element, W103_ELEMENT_MATCHER):
                lpos = self.get_metadata(
                    libcst.metadata.PositionProvider,
                    element.value.left,  # type: ignore[attr-defined]
                ).start
                self.errors.add((lpos.line, self.filename, "W103"))
