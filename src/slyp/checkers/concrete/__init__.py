from __future__ import annotations

import libcst

from .annotation_wrap import AnnotationWrapErrorCollector
from .str_concat import StrConcatErrorCollector

_VISITORS = [AnnotationWrapErrorCollector(), StrConcatErrorCollector()]


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
        for visitor in _VISITORS
        for (lineno, error_filename, code) in visitor.errors
        if error_filename == filename
    }


def _clear_visitor_errors() -> None:
    for visitor in _VISITORS:
        visitor.errors = set()
