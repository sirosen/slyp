from __future__ import annotations

import ast
import itertools
import typing as t

from ._base import ErrorRecordingVisitor


class CompareResult:
    __slots__ = ("matches", "is_trivial", "distance")

    def __init__(self, matches: bool, is_trivial: bool | None) -> None:
        self.matches = matches
        self.is_trivial = is_trivial
        self.distance = 0

    def __bool__(self) -> bool:
        return self.matches

    @property
    def adjacent(self) -> bool:
        return self.distance < 2


def is_trivial(
    node: ast.AST | list[ast.AST] | list[ast.expr] | list[ast.stmt] | None,
) -> bool:
    # if a "None" is reached during recursive descent, it means that a parent node
    # asked if one of its child elements is trivial, and there was no such element
    if node is None:
        return True
    # lists in AST are trivial if they are length 1 or 0
    # if they are length 1, their content must be trivial as well
    elif isinstance(node, list):
        if len(node) == 0:
            return True
        elif len(node) != 1:
            return False
        return is_trivial(node[0])
    # always-trivial things
    elif isinstance(node, (ast.Pass, ast.Break, ast.Continue, ast.Constant, ast.Name)):
        return True
    # trivial statements if their content is trivial
    elif isinstance(node, (ast.Return, ast.Yield)):
        return is_trivial(node.value)
    elif isinstance(node, ast.Expression):
        return is_trivial(node.body)
    elif isinstance(node, ast.Delete):
        return is_trivial(node.targets)
    elif isinstance(node, ast.Raise):
        return node.exc is None and node.cause is None
    # collections are trivial if they are empty or contain exactly one trivial item
    # this nicely matches a list check on the elements
    elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return is_trivial(node.elts)
    elif isinstance(node, ast.Dict):  # except for dict; that one has to be empty
        return len(node.keys) == 0
    # function calls are trivial if they have no keyword arguments and the argument
    # list is trivial but does not consist of nested function calls
    # i.e. this is trivial:
    #       foo(bar.baz)
    # but this is not:
    #       foo(bar(baz))
    # this is also not (nontrivial func node):
    #       foo(bar)(baz)
    elif isinstance(node, ast.Call):
        return is_trivial(node.func) and (
            node.keywords == []
            and (
                len(node.args) == 0
                or (
                    len(node.args) == 1
                    and not isinstance(node.args[0], ast.Call)
                    and is_trivial(node.args)
                )
            )
        )
    # attribute access is trivial if the value is trivial
    # i.e. in 'foo.bar', 'foo' must be trivial
    elif isinstance(node, ast.Attribute):
        return is_trivial(node.value)
    # assignments are trivial if there is only one target (not unpacking or chained) and
    # the value is trivial
    # (this intentionally does not cover AnnAssign)
    elif isinstance(node, ast.Assign):
        return (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and is_trivial(node.value)
        )
    return False


def compare_ast(
    left: ast.AST | list[ast.stmt], right: ast.AST | list[ast.stmt]
) -> CompareResult:
    if type(left) != type(right):  # noqa: E721
        return CompareResult(False, None)
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
            return CompareResult(False, None)
        return CompareResult(True, is_trivial(left))
    elif isinstance(left, list):
        if not isinstance(right, list):
            raise NotImplementedError(
                "unreachable failure on mismatched AST shape compare!"
            )
        for lvalue, rvalue in itertools.zip_longest(left, right):
            if compare_ast(lvalue, rvalue):
                continue
            return CompareResult(False, None)
        return CompareResult(True, is_trivial(left))
    else:
        res = left == right
        return CompareResult(res, is_trivial(left) if res else None)


def product_compare_ast(
    nodelist: t.Sequence[ast.AST | list[ast.stmt]],
) -> CompareResult:
    for index, item1 in enumerate(nodelist):
        for index2, item2 in enumerate(nodelist[index + 1 :]):
            if r := compare_ast(item1, item2):
                r.distance = index2 - index + 1
                return r
    return CompareResult(False, None)


def result_to_code(result: CompareResult) -> str:
    if result.adjacent:
        if result.is_trivial:
            return "W201"
        else:
            return "W200"
    else:
        if result.is_trivial:
            return "W203"
        else:
            return "W202"


class FindEquivalentBranchesVisitor(ErrorRecordingVisitor):
    # open questions:
    #
    # add support for for-else?
    #   async for-else?
    # add support for while-else?
    #   async while-else?
    #
    # others? what about bool ops like `foo() or foo()`?
    def _record(self, node: ast.AST, result: CompareResult) -> None:
        self.errors.add((node.lineno, self.filename, result_to_code(result)))

    def visit_Try(self, node: ast.Try) -> None:
        all_body_nodes: list[list[ast.stmt]] = [node.body]
        if node.handlers:
            all_body_nodes.extend(h.body for h in node.handlers)
        if node.orelse:
            all_body_nodes.append(node.orelse)
        if node.finalbody:
            all_body_nodes.append(node.finalbody)

        if r := product_compare_ast(all_body_nodes):
            self.errors.add((node.lineno, self.filename, result_to_code(r)))
        else:
            self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        if r := product_compare_ast([node.body, node.orelse]):
            self._record(node, r)
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

        if r := product_compare_ast(collected_branches):
            self._record(node, r)
        else:
            self.generic_visit(node.test)
            for subnode in node.body:
                self.generic_visit(subnode)
            for subnode in terminal_else_branch:
                self.generic_visit(subnode)
