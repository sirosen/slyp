from __future__ import annotations

import libcst

from slyp.hashable_file import HashableFile

from ._base import ErrorCollectingVisitor
from .str_concat import StrConcatErrorCollector

_VISITORS: list[ErrorCollectingVisitor] = [
    StrConcatErrorCollector(),
]


def run_cst_checkers(file_obj: HashableFile) -> set[tuple[int, str]]:
    if file_obj.parsed_cst is None:
        try:
            tree = libcst.parse_module(file_obj.binary_content)
        except (libcst.ParserSyntaxError, libcst.CSTValidationError):
            return {(0, "X001")}
    else:
        tree = file_obj.parsed_cst

    wrapper = libcst.MetadataWrapper(tree, unsafe_skip_copy=True)

    for visitor in _VISITORS:
        wrapper.visit(visitor)

    findings = {err for visitor in _VISITORS for err in visitor.errors}
    _clear_visitor_errors()
    return findings


def _clear_visitor_errors() -> None:
    for visitor in _VISITORS:
        visitor.errors = set()
