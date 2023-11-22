from __future__ import annotations

import libcst
import libcst.matchers

from ._base import ErrorCollectingVisitor

MULTILINE_SPACE_MATCHER = (
    libcst.matchers.SimpleWhitespace(
        value=libcst.matchers.MatchIfTrue(lambda x: "\n" in x)
    )
    | libcst.matchers.ParenthesizedWhitespace()
)


class AnnotationWrapErrorCollector(ErrorCollectingVisitor):
    METADATA_DEPENDENCIES = (libcst.metadata.PositionProvider,)

    def visit_Param(self, node: libcst.Param) -> None:
        if libcst.matchers.matches(
            node,
            libcst.matchers.Param(
                annotation=libcst.matchers.Annotation(
                    annotation=libcst.matchers.BinaryOperation(
                        lpar=[],
                        rpar=[],
                    )
                )
            ),
        ):
            leftmost_binop: libcst.BinaryOperation = (
                node.annotation.annotation  # type: ignore[assignment, union-attr]
            )
            while isinstance(leftmost_binop.left, libcst.BinaryOperation):
                leftmost_binop = leftmost_binop.left
            if libcst.matchers.matches(
                leftmost_binop.operator,
                libcst.matchers.BitOr(whitespace_before=MULTILINE_SPACE_MATCHER),
            ) or libcst.matchers.matches(
                leftmost_binop.operator,
                libcst.matchers.BitOr(whitespace_after=MULTILINE_SPACE_MATCHER),
            ):
                lpos = self.get_metadata(
                    libcst.metadata.PositionProvider, leftmost_binop
                ).start
                self.errors.add((lpos.line, self.filename, "W120"))
