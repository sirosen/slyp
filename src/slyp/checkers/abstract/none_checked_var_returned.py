from __future__ import annotations

import ast

from ._base import ErrorRecordingVisitor


class NoneCheckedVarReturnVisitor(ErrorRecordingVisitor):
    def visit_If(self, node: ast.If) -> None:
        if _is_var_none_check(node.test):
            var_name = node.test.left.id  # type: ignore[attr-defined]
            if _is_return_var(node.body, var_name):
                self.errors.add((node.lineno, self.filename, "E110"))
                return
        self.generic_visit(node)


def _is_var_none_check(node: ast.expr) -> bool:
    return (
        isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Name)
        and len(node.ops) == 1
        and isinstance(node.ops[0], ast.Is)
        and len(node.comparators) == 1
        and isinstance(node.comparators[0], ast.Constant)
        and node.comparators[0].value is None
    )


def _is_return_var(body: list[ast.stmt], var_name: str) -> bool:
    return (
        len(body) == 1
        and isinstance(body[0], ast.Return)
        and isinstance(body[0].value, ast.Name)
        and body[0].value.id == var_name
    )
