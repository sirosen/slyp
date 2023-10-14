from __future__ import annotations

import ast
import itertools
import typing as t


def compare_ast(
    left: ast.AST | list[ast.stmt], right: ast.AST | list[ast.stmt]
) -> bool:
    if type(left) != type(right):  # noqa: E721
        return False
    if isinstance(left, ast.AST):
        if not isinstance(right, ast.AST):
            raise NotImplementedError(
                "unreachable failure on mismatched AST shape compare!"
            )
        for lfield, rfield in itertools.zip_longest(
            ast.iter_fields(left), ast.iter_fields(right)
        ):
            lname, lvalues = lfield
            rname, rvalues = rfield
            if lname == rname and compare_ast(lvalues, rvalues):
                continue
            return False
        return True
    elif isinstance(left, list):
        if not isinstance(right, list):
            raise NotImplementedError(
                "unreachable failure on mismatched AST shape compare!"
            )
        for lvalue, rvalue in itertools.zip_longest(left, right):
            if compare_ast(lvalue, rvalue):
                continue
            return False
        return True
    else:
        return left == right


def product_compare_ast(nodelist: t.Sequence[ast.AST | list[ast.stmt]]) -> bool:
    for index, item1 in enumerate(nodelist):
        for item2 in nodelist[index + 1 :]:
            if compare_ast(item1, item2):
                return True
    return False


class FindEquivalentBranchesVisitor(ast.NodeVisitor):
    # open questions:
    #
    # add support for for-else?
    #   async for-else?
    # add support for while-else?
    #   async while-else?
    #
    # others? what about bool ops like `foo() or foo()`?
    def __init__(self) -> None:
        super().__init__()
        self.filename: str = "<unset>"
        self.errors: set[tuple[int, str, str]] = set()

    def visit_Try(self, node: ast.Try) -> None:
        all_body_nodes: list[list[ast.stmt]] = [node.body]
        if node.handlers:
            all_body_nodes.extend(h.body for h in node.handlers)
        if node.orelse:
            all_body_nodes.append(node.orelse)
        if node.finalbody:
            all_body_nodes.append(node.finalbody)

        if product_compare_ast(all_body_nodes):
            self.errors.add((node.lineno, self.filename, "W200"))
        else:
            self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        if product_compare_ast([node.body, node.orelse]):
            self.errors.add((node.lineno, self.filename, "W200"))
        else:
            self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        collected_branches = [node.body]

        current: list[ast.stmt] = node.orelse
        while len(current) == 1 and isinstance(current[0], ast.If):
            inner_if = current[0]
            collected_branches.append(inner_if.body)
            current = inner_if.orelse
        collected_branches.append(current)
        terminal_else_branch = current  # rename for clarity below

        if product_compare_ast(collected_branches):
            self.errors.add((node.lineno, self.filename, "W200"))
        else:
            self.generic_visit(node.test)
            for subnode in node.body:
                self.generic_visit(subnode)
            for subnode in terminal_else_branch:
                self.generic_visit(subnode)
