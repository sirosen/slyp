from __future__ import annotations

import ast
import typing as t

from slyp.hashable_file import HashableFile

from ._base import ErrorRecordingVisitor
from .matching_branches import FindEquivalentBranchesVisitor

_VISITORS: t.Sequence[ErrorRecordingVisitor] = [
    FindEquivalentBranchesVisitor(),
]


def run_ast_checkers(file_obj: HashableFile) -> set[tuple[int, str]]:
    try:
        tree = ast.parse(file_obj.binary_content, filename=file_obj.filename)
    except SyntaxError:
        return {(0, "X001")}

    for visitor in _VISITORS:
        visitor.visit(tree)

    findings = {err for visitor in _VISITORS for err in visitor.errors}
    _clear_visitor_errors()
    return findings


def _clear_visitor_errors() -> None:
    for visitor in _VISITORS:
        visitor.errors = set()
