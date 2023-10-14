from __future__ import annotations

import re

from .abstract import run_ast_checkers
from .concrete import run_cst_checkers

CODE_MAP = {
    # internal codes
    "X001": "unparsable file",
    # external codes
    "E100": "unnecessary string concat",
    "E101": "unparenthesized multiline string concat in keyword arg",
    "E102": "unparenthesized multiline string concat in dict value",
    "E103": "unparenthesized multiline string concat in collection type",
    "W200": "two AST branches have identical contents",
}

_DISALBE_RE = re.compile(rb"#\s*slyp:\s*disable=(.*)")


def check_file(filename: str, *, verbose: bool, disabled_codes: set[str]) -> bool:
    if verbose:
        print(f"checking {filename}")

    with open(filename, "rb") as fp:
        bin_data = fp.read()

    cst_errors = run_cst_checkers(filename, bin_data)
    ast_errors = run_ast_checkers(filename, bin_data)
    errors = sorted(cst_errors | ast_errors)

    lines = bin_data.splitlines()
    filtered_errors = sorted(
        (lineno, code)
        for lineno, code in errors
        if code not in disabled_codes and not (_exempt(lines, lineno - 1, code))
    )

    if filtered_errors:
        for lineno, code in filtered_errors:
            print(f"{filename}:{lineno}: {CODE_MAP[code]} ({code})")
        return False
    return True


def _exempt(lines: list[bytes], lineno: int, code: str) -> bool:
    # should be impossible most of the time, but a failed parse uses a position of
    # 0 which becomes -1 here
    if lineno == -1 or len(lines) < lineno:
        return False

    line = lines[lineno]
    # start with a faster check before trying the regex
    if b"slyp" not in line:
        return False

    if match := _DISALBE_RE.search(line):
        disabled_codes = match.group(1)
        return disabled_codes == b"all" or code.encode() in disabled_codes.split(b",")

    return False
