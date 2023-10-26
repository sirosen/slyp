from __future__ import annotations

import libcst
import libcst.matchers

MULTILINE_SPACE_MATCHER = (
    libcst.matchers.SimpleWhitespace(
        value=libcst.matchers.MatchIfTrue(lambda x: "\n" in x)
    )
    | libcst.matchers.ParenthesizedWhitespace()
)


class AnnotationWrapErrorCollector(libcst.CSTVisitor):
    METADATA_DEPENDENCIES = (libcst.metadata.PositionProvider,)

    def __init__(self) -> None:
        super().__init__()
        self.filename: str = "<unset>"
        self.errors: set[tuple[int, str, str]] = set()

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
            leftmost_binop = node.annotation.annotation
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
