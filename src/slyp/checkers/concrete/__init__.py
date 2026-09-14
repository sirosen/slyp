from __future__ import annotations

import libcst

from slyp.hashable_file import HashableFile

from ._visitor import ErrorCollector


def run_cst_checkers(file_obj: HashableFile) -> set[tuple[int, str]]:
    if file_obj.parsed_cst is None:
        try:
            module = libcst.parse_module(file_obj.binary_content)
        except (libcst.ParserSyntaxError, libcst.CSTValidationError):
            return {(0, "X001")}
    else:
        module = file_obj.parsed_cst

    visitor = ErrorCollector(module)
    module.visit(visitor)
    return visitor.errors
