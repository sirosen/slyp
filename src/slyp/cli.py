from __future__ import annotations

import argparse
import sys
import textwrap

from slyp.codes import CODE_MAP
from slyp.driver import driver_main


def main() -> None:
    parser = argparse.ArgumentParser(
        description="slyp is a linter and fixer for Python code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--list", action="store_true", help="list all error and warning codes"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        help="increase output verbosity",
        default=0,
        dest="verbosity",
    )
    parser.add_argument(
        "--use-git-ls", action="store_true", help="find python files from git-ls-files"
    )
    parser.add_argument(
        "--only",
        choices=("fix", "lint"),
        help="Only fix or only lint.",
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
    parser.add_argument(
        "--no-cache",
        help="Disable caching of results in the '.slyp_cache' directory.",
        action="store_true",
    )
    parser.add_argument("files", nargs="*", help="default: all python files")
    args = parser.parse_args()

    if args.list:
        list_codes()
        sys.exit(0)

    if args.use_git_ls and args.files:
        parser.error("--use-git-ls requires no filenames as arguments")

    if "-" in args.files:
        if len(args.files) > 1:
            parser.error("stdin can only be used with one file at a time")
        if args.only is None:
            parser.error("stdin mode requires '--only' to be set")

    success = driver_main(args)

    if not success:
        sys.exit(1)

    if args.verbosity:
        print("ok")


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
