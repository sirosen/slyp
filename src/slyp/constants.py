import typing as t

DEFAULT_DISABLED_CODES: frozenset[str] = frozenset(
    (
        "W201",
        "W202",
        "W203",
    )
)
CONTRACT_VERSION: str = "1.7"

ValidMode: t.TypeAlias = t.Literal["list_codes", "lint", "fix", "default"]
