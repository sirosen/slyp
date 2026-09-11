import argparse

from slyp.constants import DEFAULT_DISABLED_CODES, ValidMode
from slyp.driver import SlypArgs


def to_driver_args(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> SlypArgs:
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

    return SlypArgs(
        mode=mode,
        verbosity=args.verbose - args.quiet,
        use_git_ls=args.use_git_ls,
        disabled_codes=disabled_codes,
        enabled_codes=enabled_codes,
        no_cache=args.no_cache,
        files=args.files,
    )


def parse_args(argv: list[str]) -> SlypArgs:
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

    return to_driver_args(parser, args)
