from __future__ import annotations

import argparse
import glob
import os
import stat
import subprocess
import sys
import typing as t

from slyp.checkers import check_file

HELP = """
slyp primarily checks for flavors of string concatenation which are allowed by
the `black` formatter and other linting tools, but are either unnecessary or
potentially confusing.

E100: unnecessary string concat
    x = "foo " "bar"

E101: unparenthesized multiline string concat in keyword arg
    foo(
        bar="alpha "
        "beta"
    )

E102: unparenthesized multiline string concat in dict value
    {
        "foo": "alpha "
        "beta"
    }

E103: unparenthesized multiline string concat in collection type
    x = (  # a tuple
        "alpha "
        "beta",
        "gamma"
    )
    x = {  # or a set
        "alpha "
        "beta",
        "gamma"
    }

W200: two AST branches have identical contents
    if x is True:
        return y + 1
    else:
        # some comment
        return y + 1
"""


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
        help="disable error and warning codes (comma delimited)",
    )
    parser.add_argument("files", nargs="*", help="default: all python files")
    args = parser.parse_args()
    if args.use_git_ls and args.files:
        parser.error("--use-git-ls requires no filenames as arguments")

    if args.disable:
        disabled_codes = set(args.disable.split(","))
    else:
        disabled_codes = set()

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
