from __future__ import annotations

import re

import libcst

from slyp.hashable_file import HashableFile
from slyp.models import Message, Result

from .transformer import SlypTransformer

_DISALBE_RE = re.compile(rb"#\s*((slyp:\s*disable(\=format)?)|(fmt:\s*off))(\s|$)")
_ENABLE_RE = re.compile(rb"#\s*((slyp:\s*enable(\=format)?)|(fmt:\s*on))(\s|$)")


def fix_file(file_obj: HashableFile) -> Result:
    try:
        new_data, parsed_cst = _fix_data(file_obj.binary_content)
    # ignore failures to parse and treat these as "unchanged"
    # linting will flag these independently
    except (RecursionError, libcst.ParserSyntaxError, libcst.CSTValidationError):
        return Result(
            success=False,
            messages=[
                Message(f"slyp: failed to parse {file_obj.filename}", verbosity=1)
            ],
        )

    file_obj.parsed_cst = parsed_cst

    if new_data == file_obj.binary_content:
        if file_obj.is_stdio:
            file_obj.write(file_obj.binary_content)
        return Result(
            messages=[Message(f"slyp: no changes to {file_obj.filename}", verbosity=1)],
            success=True,
        )

    file_obj.write(new_data)
    return Result(messages=[Message(f"slyp: fixed {file_obj.filename}")], success=False)


def _fix_data(content: bytes) -> tuple[bytes, libcst.Module]:
    disabled_line_ranges = _find_disabled_ranges(content)
    module = libcst.parse_module(content)

    transformer = SlypTransformer(module, disabled_line_ranges)
    tree = module.visit(transformer)

    if not transformer.made_changes:
        return content, tree
    return tree.code.encode(tree.encoding), tree


def _find_disabled_ranges(content: bytes) -> list[tuple[int, int | float]]:
    start_locations = []
    end_locations = []
    for lineno, line in enumerate(content.split(b"\n")):
        if _DISALBE_RE.search(line):
            start_locations.append(lineno)
        if _ENABLE_RE.search(line):
            end_locations.append(lineno)

    ranges: list[tuple[int, int | float]] = []
    for start in start_locations:
        for end in end_locations:
            if end > start:
                ranges.append((start, end))
                break
        else:
            ranges.append((start, float("inf")))
    return ranges
