from __future__ import annotations

import ast
import typing as t

from ._base import ErrorRecordingVisitor
from .matching_branches import FindEquivalentBranchesVisitor
from .none_checked_var_returned import NoneCheckedVarReturnVisitor

_VISITORS: t.Sequence[ErrorRecordingVisitor] = [
    FindEquivalentBranchesVisitor(),
    NoneCheckedVarReturnVisitor(),
]


def run_ast_checkers(filename: str, content: bytes) -> set[tuple[int, str]]:
    try:
        tree = ast.parse(content, filename=filename)
    except SyntaxError:
        return {(0, "X001")}

    for visitor in _VISITORS:
        visitor.filename = filename
        visitor.visit(tree)
    return {
        (lineno, code)
        for visitor in _VISITORS
        for (lineno, error_filename, code) in visitor.errors
        if error_filename == filename
    }


def _clear_visitor_errors() -> None:
    for visitor in _VISITORS:
        visitor.errors = set()
