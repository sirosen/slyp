from __future__ import annotations

import sys
import textwrap

from slyp.codes import CODE_MAP
from slyp.driver import driver_main

from ._parse import parse_args


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if args.mode == "list_codes":
        list_codes()
        sys.exit(0)

    success = driver_main(args)

    if not success:
        sys.exit(1)

    if args.verbosity > 0:
        print("ok", file=sys.stderr)


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
