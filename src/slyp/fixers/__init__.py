from __future__ import annotations

import libcst

from .unnecessary_parens import UnnecessaryParenthesesFixer

_FIXERS: list[libcst.CSTTransformer] = [
    UnnecessaryParenthesesFixer(),
]


def fix_file(filename: str, *, verbose: bool, apply: bool = False) -> bool:
    """returns True if no changes were needed"""
    with open(filename, "rb") as fp:
        bin_data = fp.read()

    try:
        new_data = _fix_data(bin_data)
    # ignore failures to parse and treat these as "unchanged"
    # linting will flag these independently
    except (RecursionError, libcst.ParserSyntaxError):
        new_data = bin_data

    if new_data == bin_data:
        if verbose:
            print(f"fixing {filename} made no changes")

        return True

    print(f"fixing {filename}")
    with open(filename, "wb") as fp:
        fp.write(new_data)

    return False


def _fix_data(content: bytes) -> bytes:
    raw_tree = libcst.parse_module(content)
    tree = libcst.MetadataWrapper(raw_tree)

    for fixer in _FIXERS:
        tree = tree.visit(fixer)

    return tree.code.encode("utf-8")
