from . import _inline_modules, _stdlib_modules

MODULES: dict[str, bytes] = {
    "stdlib_csv": _stdlib_modules.CSV_SOURCE,
    "stdlib_textwrap": _stdlib_modules.TEXTWRAP_SOURCE,
    "trivial": _inline_modules.TRIVIAL_MODULE,
    "small": _inline_modules.SMALL_MODULE,
    "simple_cli_parser": _inline_modules.SIMPLE_CLI_PARSER_MODULE,
}
