from __future__ import annotations

import libcst

from slyp.hashable_file import HashableFile

from ._base import ErrorCollectingVisitor
from .str_concat import StrConcatErrorCollector

_VISITORS: list[ErrorCollectingVisitor] = [
    StrConcatErrorCollector(),
]


def run_cst_checkers(file_obj: HashableFile) -> set[tuple[int, str]]:
    try:
        tree = libcst.parse_module(file_obj.binary_content)
    except (libcst.ParserSyntaxError, libcst.CSTValidationError):
        return {(0, "X001")}
    wrapper = libcst.MetadataWrapper(tree)
    for visitor in _VISITORS:
        visitor.filename = file_obj.filename
        wrapper.visit(visitor)
    return {
        (lineno, code)
        for visitor in _VISITORS
        for (lineno, error_filename, code) in visitor.errors
        if error_filename == file_obj.filename
    }


def _clear_visitor_errors() -> None:
    for visitor in _VISITORS:
        visitor.errors = set()
