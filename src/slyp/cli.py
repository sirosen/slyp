from __future__ import annotations

import argparse
import glob
import json
import os
import stat
import subprocess
import sys
import textwrap
import time
import typing as t

from slyp.checkers import check_file
from slyp.codes import CODE_MAP
from slyp.fixers import fix_file

DEFAULT_DISABLED_CODES: set[str] = {"W201", "W202", "W203"}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="slyp is a linter and fixer for Python code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--list", action="store_true", help="list all error and warning codes"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="increase output verbosity"
    )
    # hidden option for quick-and-dirty profiling
    parser.add_argument("--debug-timings", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--use-git-ls", action="store_true", help="find python files from git-ls-files"
    )
    parser.add_argument(
        "--disable",
        help="Disable error and warning codes (comma delimited)",
        default="",
    )
    parser.add_argument(
        "--enable",
        help=(
            "Enable error and warning codes which are otherwise disabled "
            "(comma delimited, overrides --disable)"
        ),
        default="",
    )
    parser.add_argument("files", nargs="*", help="default: all python files")
    args = parser.parse_args()

    if args.list:
        list_codes()
        sys.exit(0)

    if args.use_git_ls and args.files:
        parser.error("--use-git-ls requires no filenames as arguments")

    # parse inputs from comma delimited lists
    disabled_codes = {x for x in args.disable.split(",") if x != ""}
    enabled_codes = {x for x in args.enable.split(",") if x != ""}
    # add default disables if "all" is not in --enable
    if "all" not in enabled_codes:
        disabled_codes = disabled_codes | DEFAULT_DISABLED_CODES

    success = True
    timings = {}
    for filename in all_py_filenames(args.files, args.use_git_ls):
        start = time.time()
        success = fix_file(filename, verbose=args.verbose) and success
        after_fix = time.time()
        success = (
            check_file(
                filename,
                verbose=args.verbose,
                disabled_codes=disabled_codes,
                enabled_codes=enabled_codes,
            )
            and success
        )
        after_check = time.time()
        timings[filename] = {
            "fix": after_fix - start,
            "check": after_check - after_fix,
        }
    if args.debug_timings:
        print(json.dumps(timings, indent=2, separators=(",", ": ")))

    if not success:
        sys.exit(1)

    if args.verbose:
        print("ok")


def all_py_filenames(files: t.Sequence[str], use_git_ls: bool) -> t.Iterable[str]:
    if files:
        yield from files
    elif use_git_ls:
        git_ls_files_proc = subprocess.run(
            ["git", "ls-files"], check=True, capture_output=True, text=True
        )
        candidates = git_ls_files_proc.stdout.split("\n")
        for file in candidates:
            if file == "":
                continue
            if is_python(file):
                yield file
    else:
        yield from glob.glob("**/*.py", recursive=True)


def is_python(filename: str) -> bool:
    # don't pay attention to symlinks or other special filetypes
    # those aren't really files to check
    # but you might be fed them by `git ls-files`
    if not stat.S_ISREG(os.lstat(filename).st_mode):
        return False

    # .py is good
    if filename.endswith(".py"):
        return True

    # if it's not executable, it couldn't be a script
    if not os.access(filename, os.X_OK):
        return False

    # but otherwise, look for a shebang which contains 'python' as a substring
    try:
        with open(filename, encoding="utf-8") as fp:
            firstline = fp.readline()
    except UnicodeDecodeError:
        return False
    if firstline.startswith("#!") and "python" in firstline:
        return True

    return False


def list_codes() -> None:
    first = True
    for code in CODE_MAP.values():
        if code.hidden:
            continue
        if first:
            first = False
        else:
            print()

        if code.default_disabled:
            description: str = f"{code.message} (disabled by default)"
        else:
            description = code.message
        print(f"{code.code}: {description}")
        print(textwrap.indent(code.example, "    "))
