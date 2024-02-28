from __future__ import annotations

import libcst

from slyp.hashable_file import HashableFile
from slyp.result import Message, Result

from .transformer import SlypTransformer


def fix_file(file_obj: HashableFile) -> Result:
    """returns True if no changes were needed"""
    try:
        new_data = _fix_data(file_obj.binary_content)
    # ignore failures to parse and treat these as "unchanged"
    # linting will flag these independently
    except (RecursionError, libcst.ParserSyntaxError, libcst.CSTValidationError):
        return Result(success=True, messages=[])

    if new_data == file_obj.binary_content:
        return Result(
            messages=[
                Message(
                    f"slyp: no changes to {file_obj.filename}", verbosity=1, priority=0
                )
            ],
            success=True,
        )

    file_obj.write(new_data)
    return Result(
        messages=[Message(f"slyp: fixed {file_obj.filename}", priority=0)],
        success=False,
    )


def _fix_data(content: bytes) -> bytes:
    raw_tree = libcst.parse_module(content)
    tree = libcst.MetadataWrapper(raw_tree)

    tree = tree.visit(SlypTransformer())  # type: ignore[assignment]

    code: str = tree.code  # type: ignore[attr-defined]
    return code.encode(tree.encoding)  # type: ignore[attr-defined]
