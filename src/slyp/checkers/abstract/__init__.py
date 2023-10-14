from __future__ import annotations

import ast

from .matching_branches import FindEquivalentBranchesVisitor

_VISITORS = [FindEquivalentBranchesVisitor()]


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
        for (lineno, error_filename, code) in visitor.errors
        if error_filename == filename
        for visitor in _VISITORS
    }
