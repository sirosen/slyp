from __future__ import annotations

import inspect

import pytest

from slyp.checkers import _clear_errors


# use stdlib modules as sample inputs of significant size
@pytest.fixture(scope="session", params=["configparser", "textwrap"])
def stdlib_module_source(request) -> bytes:
    mod = __import__(request.param)
    return inspect.getsource(mod).encode()


@pytest.fixture(autouse=True)
def _reset_checker_state():
    _clear_errors()
