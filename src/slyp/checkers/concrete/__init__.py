from __future__ import annotations
import libcst
from .str_concat import StrConcatErrorCollector


def run_cst_checkers(filename: str) -> set[tuple[int, str]]:
    visitors = [StrConcatErrorCollector()]
    with open(filename) as fp:
        try:
            tree = libcst.parse_module(fp.read())
        except libcst.ParserSyntaxError:
            return {(0, "X001")}
    wrapper = libcst.MetadataWrapper(tree)
    for visitor in visitors:
        wrapper.visit(visitor)
    return {e for e in visitor.errors for visitor in visitors}
