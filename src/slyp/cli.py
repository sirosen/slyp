from __future__ import annotations

import argparse
import glob
import os
import stat
import subprocess
import sys
import textwrap
import typing as t

from slyp.checkers import check_file
from slyp.codes import CODE_MAP

DEFAULT_DISABLED_CODES: set[str] = {"W201", "W202", "W203"}

HELP = """
slyp is a linter which checks for stylistic issues in Python code which may be
correctness problems or opportunities for improvement
"""

for code in CODE_MAP.values():
    if code.hidden:
        continue
    HELP += f"""

{code.code}: {code.message}{"(disabled by default)" if code.default_disabled else ""}
{textwrap.indent(code.example, "    ")}"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description=HELP, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="increase output verbosity"
    )
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
    if args.use_git_ls and args.files:
        parser.error("--use-git-ls requires no filenames as arguments")

    disabled_codes = {x for x in args.disable.split(",") if x != ""}
    disabled_codes = disabled_codes | DEFAULT_DISABLED_CODES
    enabled_codes = {x for x in args.enable.split(",") if x != ""}
    disabled_codes = disabled_codes - enabled_codes

    success = True
    for filename in all_py_filenames(args.files, args.use_git_ls):
        success = (
            check_file(filename, verbose=args.verbose, disabled_codes=disabled_codes)
            and success
        )

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
    with open(filename, encoding="utf-8") as fp:
        firstline = fp.readline()
    if firstline.startswith("#!") and "python" in firstline:
        return True

    return False
