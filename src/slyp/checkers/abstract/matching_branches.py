from __future__ import annotations

import ast
import itertools


def compare_ast(left, right):
    if type(left) != type(right):  # noqa: #721
        return False
    if isinstance(left, ast.AST):
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
        for lvalue, rvalue in itertools.zip_longest(left, right):
            if compare_ast(lvalue, rvalue):
                continue
            return False
        return True
    else:
        return left == right


def product_compare_ast(nodelist) -> bool:
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
    def __init__(self):
        super().__init__()
        self.errors = []

    def visit_Try(self, node):
        all_body_nodes = [node.body]
        if node.handlers:
            all_body_nodes.extend(h.body for h in node.handlers)
        if node.orelse:
            all_body_nodes.append(node.orelse)
        if node.finalbody:
            all_body_nodes.append(node.finalbody)

        if product_compare_ast(all_body_nodes):
            self.errors.append((node.lineno, "W200"))
        else:
            self.generic_visit(node)

    def visit_IfExp(self, node):
        if product_compare_ast([node.body, node.orelse]):
            self.errors.append((node.lineno, "W200"))
        else:
            self.generic_visit(node)

    def visit_If(self, node):
        collected_branches = [node.body]

        current = node.orelse
        while len(current) == 1 and isinstance(current[0], ast.If):
            current = current[0]
            collected_branches.append(current.body)
            current = current.orelse
        collected_branches.append(current)
        terminal_else_branch = current  # rename for clarity below

        if product_compare_ast(collected_branches):
            self.errors.append((node.lineno, "W200"))
        else:
            self.generic_visit(node.test)
            for subnode in node.body:
                self.generic_visit(subnode)
            for subnode in terminal_else_branch:
                self.generic_visit(subnode)
