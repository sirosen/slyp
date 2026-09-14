from __future__ import annotations

import inspect


def _load_source(modname: str) -> bytes:
    mod = __import__(modname)
    return inspect.getsource(mod).encode()


CSV_SOURCE = _load_source("csv")
TEXTWRAP_SOURCE = _load_source("textwrap")
