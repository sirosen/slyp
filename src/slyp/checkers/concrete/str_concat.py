from __future__ import annotations

import libcst
import libcst.matchers

from ._base import ErrorCollectingVisitor

# SimpleWhitespace defines whitespace as seen between tokens in most contexts
# it can contain newlines *if* there is a preceding backslash escape
SIMPLE_WHITESPACE_NO_NEWLINE_MATCHER = libcst.matchers.SimpleWhitespace(
    value=libcst.matchers.MatchIfTrue(lambda x: "\n" not in x)
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
