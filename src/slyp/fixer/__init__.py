from __future__ import annotations

import libcst

from .transformer import SlypTransformer


def fix_file(filename: str, *, verbose: bool) -> bool:
    """returns True if no changes were needed"""
    with open(filename, "rb") as fp:
        bin_data = fp.read()

    try:
        new_data = _fix_data(bin_data)
    # ignore failures to parse and treat these as "unchanged"
    # linting will flag these independently
    except (RecursionError, libcst.ParserSyntaxError, libcst.CSTValidationError):
        return True

    if new_data == bin_data:
        if verbose:
            print(f"slyp: no changes to {filename}")

        return True

    print(f"slyp: fixing {filename}")
    with open(filename, "wb") as fp:
        fp.write(new_data)

    return False


def _fix_data(content: bytes) -> bytes:
    raw_tree = libcst.parse_module(content)
    tree = libcst.MetadataWrapper(raw_tree)

    tree = tree.visit(SlypTransformer())  # type: ignore[assignment]

    code: str = tree.code  # type: ignore[attr-defined]
    return code.encode(tree.encoding)  # type: ignore[attr-defined]
