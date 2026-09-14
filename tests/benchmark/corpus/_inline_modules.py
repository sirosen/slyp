TRIVIAL_MODULE = b"""\
x = 1
"""

SMALL_MODULE = b"""\
def foo(x: int) -> int:
    if not isinstance(x, int):
        raise TypeError(f"bad x, expected int, got {x.__class__.__name__!r}")
    return _foo(x)

def _foo(x: int) -> int:
    return (x + 1) ** 2
"""

# a copy of the Slyp CLI Parser, at time of writing
SIMPLE_CLI_PARSER_MODULE = b'''\
import argparse

from slyp.constants import DEFAULT_DISABLED_CODES, ValidMode
from slyp.models import SlypRequest


def parse_args(argv: list[str]) -> SlypRequest:
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
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="count",
        help="decrease output verbosity",
        default=0,
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
    args = parser.parse_args(argv)

    return args_to_request(parser, args)


def args_to_request(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> SlypRequest:
    """
    Translate argparse results to this nicely typed structure and handle
    any conflicts or other usage errors.
    """
    mode: ValidMode = "default"
    if args.list:
        mode = "list_codes"
    elif args.only:
        mode = args.only

    if args.use_git_ls and args.files:
        parser.error("--use-git-ls requires no filenames as arguments")

    if "-" in args.files:
        if len(args.files) > 1:
            parser.error("stdin can only be used with one file at a time")
        if args.only is None:
            parser.error("stdin mode requires '--only' to be set")

    disabled_codes = {x for x in args.disable.split(",") if x != ""}
    enabled_codes = {x for x in args.enable.split(",") if x != ""}
    # add default disables if "all" is not in --enable
    if "all" not in enabled_codes:
        disabled_codes = disabled_codes | DEFAULT_DISABLED_CODES

    return SlypRequest(
        mode=mode,
        verbosity=args.verbose - args.quiet,
        use_git_ls=args.use_git_ls,
        disabled_codes=disabled_codes,
        enabled_codes=enabled_codes,
        no_cache=args.no_cache,
        files=args.files,
    )
'''
