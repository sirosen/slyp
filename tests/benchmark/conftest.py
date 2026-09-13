from __future__ import annotations

import inspect

import pytest


# use stdlib modules as sample inputs of significant size
@pytest.fixture(scope="session", params=["configparser", "textwrap"])
def stdlib_module_source(request) -> bytes:
    mod = __import__(request.param)
    return inspect.getsource(mod).encode()
