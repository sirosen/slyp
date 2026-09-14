from __future__ import annotations

import libcst
import libcst.matchers

from slyp.lazy_cst import LazyCSTNodePositions

# SimpleWhitespace defines whitespace as seen between tokens in most contexts
# it can contain newlines *if* there is a preceding backslash escape
SIMPLE_WHITESPACE_NO_NEWLINE_MATCHER = libcst.matchers.SimpleWhitespace(
    value=libcst.matchers.MatchIfTrue(lambda x: "\n" not in x)
)


class ErrorCollector(libcst.CSTVisitor):
    def __init__(self, module: libcst.Module) -> None:
        self.errors: set[tuple[int, str]] = set()
        # lazy position metadata
        self.positions = LazyCSTNodePositions(module)

    # explicitly disable attribute visiting to save work
    def on_visit_attribute(self, node: libcst.CSTNodeT, attribute: str) -> None:
        pass

    def on_leave_attribute(self, node: libcst.CSTNodeT, attribute: str) -> None:
        pass

    # simplify on_leave as a micro-optimization
    def on_leave(self, original_node: libcst.CSTNodeT) -> None:
        pass

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
            lpos = self.positions.lookup(node.left).start
            self.errors.add((lpos.line, "E100"))

    def visit_BinaryOperation(self, node: libcst.BinaryOperation) -> None:
        # check for 'unnecessary string concat' situations with explicit `+`
        # e.g.
        #   x = "foo " + "bar"
        if libcst.matchers.matches(
            node,
            libcst.matchers.BinaryOperation(
                operator=libcst.matchers.Add(),
                left=libcst.matchers.OneOf(
                    libcst.matchers.SimpleString(),
                    libcst.matchers.ConcatenatedString(),
                    libcst.matchers.FormattedString(),
                ),
                right=libcst.matchers.OneOf(
                    libcst.matchers.SimpleString(),
                    libcst.matchers.ConcatenatedString(),
                    libcst.matchers.FormattedString(),
                ),
            ),
        ):
            lpos = self.positions.lookup(node.left).end
            rpos = self.positions.lookup(node.right).start
            if lpos.line == rpos.line:
                self.errors.add((lpos.line, "E101"))
