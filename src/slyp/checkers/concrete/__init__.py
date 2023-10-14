from __future__ import annotations

import libcst

from .str_concat import StrConcatErrorCollector

_VISITORS = [StrConcatErrorCollector()]


def run_cst_checkers(filename: str, content: bytes) -> set[tuple[int, str]]:
    try:
        tree = libcst.parse_module(content)
    except libcst.ParserSyntaxError:
        return {(0, "X001")}
    wrapper = libcst.MetadataWrapper(tree)
    for visitor in _VISITORS:
        visitor.filename = filename
        wrapper.visit(visitor)
    return {
        (lineno, code)
        for (lineno, error_filename, code) in visitor.errors
        if error_filename == filename
        for visitor in _VISITORS
    }
