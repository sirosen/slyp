from __future__ import annotations
from .str_concat import StrConcatErrorCollector
import libcst

ERROR_MAP = {
    "E100": "unnecessary string concat",
    "E101": "unparenthesized multiline string concat in keyword arg",
    "E102": "unparenthesized multiline string concat in dict value",
    "E103": "unparenthesized multiline string concat in collection type",
    "E200": "two AST branches have identical contents",
}


def check_file(
    filename: str, *, quiet: bool, disabled_codes: set[str] | None = None
) -> bool:
    if not quiet:
        print(f"checking {filename}")
    visitor = StrConcatErrorCollector()
    with open(filename) as fp:
        tree = libcst.parse_module(fp.read())
    wrapper = libcst.MetadataWrapper(tree)
    wrapper.visit(visitor)
    errors = sorted(visitor.errors)

    disabled_codes = disabled_codes or {}

    if errors:
        for lineno, code in errors:
            if code in disabled_codes:
                continue
            print(f"{filename}:{lineno}: {ERROR_MAP[code]} ({code})")
        return False
    return True
