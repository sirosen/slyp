from __future__ import annotations

import ast

from .matching_branches import FindEquivalentBranchesVisitor


def run_ast_checkers(filename: str) -> set[tuple[int, str]]:
    visitors = [FindEquivalentBranchesVisitor()]
    with open(filename) as fp:
        try:
            tree = ast.parse(fp.read(), filename=filename)
        except SyntaxError:
            return {(0, "X001")}

    for visitor in visitors:
        visitor.visit(tree)
    return {e for e in visitor.errors for visitor in visitors}
