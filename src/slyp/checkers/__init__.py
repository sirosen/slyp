from __future__ import annotations

import re

from slyp.codes import CODE_MAP

from .abstract import run_ast_checkers
from .concrete import run_cst_checkers

_DISALBE_RE = re.compile(rb"#\s*slyp:\s*disable=(.*)")


def check_file(
    filename: str, *, verbose: bool, disabled_codes: set[str], enabled_codes: set[str]
) -> bool:
    if verbose:
        print(f"checking {filename}")

    with open(filename, "rb") as fp:
        bin_data = fp.read()

    try:
        cst_errors = run_cst_checkers(filename, bin_data)
    except RecursionError:
        cst_errors = {(0, "X002")}

    ast_errors = run_ast_checkers(filename, bin_data)
    errors = sorted(cst_errors | ast_errors)

    lines = bin_data.splitlines()
    filtered_errors = sorted(
        (lineno, code)
        for lineno, code in errors
        if not _disabled(code, disabled_codes, enabled_codes)
        and not _exempt(lines, lineno - 1, code)
    )

    if filtered_errors:
        for lineno, code in filtered_errors:
            print(f"{filename}:{lineno}: {CODE_MAP[code]}")
        return False
    return True


def _disabled(code: str, disabled_codes: set[str], enabled_codes: set[str]) -> bool:
    cdef = CODE_MAP[code]

    # enabled is higher precedence than disabled
    # but "all" in enabled_codes is not checked so that
    # '--enable all --disable FOO' works
    if code in enabled_codes or cdef.category in enabled_codes:
        return False

    # if "all" is in disabled_codes, then everything is disabled unless
    # explicitly enabled (checked above)
    if (
        "all" in disabled_codes
        or code in disabled_codes
        or cdef.category in disabled_codes
    ):
        return True

    return False


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


def _clear_errors() -> None:
    # testsuite hook for resetting errors for clean reporting
    from .abstract import _clear_visitor_errors as clear_cst_errors
    from .concrete import _clear_visitor_errors as clear_ast_errors

    clear_cst_errors()
    clear_ast_errors()
