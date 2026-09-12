from __future__ import annotations

import dataclasses
import typing as t

from slyp.constants import ValidMode


@dataclasses.dataclass(slots=True)
class SlypRequest:
    """Fully normalized arguments, as parsed from the CLI."""

    mode: ValidMode
    verbosity: int
    use_git_ls: bool
    disabled_codes: set[str]
    enabled_codes: set[str]
    no_cache: bool
    files: t.Sequence[str]
