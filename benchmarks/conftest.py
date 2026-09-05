from __future__ import annotations

import pathlib

import pytest

from slyp.checkers import _clear_errors
from slyp.hashable_file import HashableFile

DATA_DIR = pathlib.Path(__file__).parent / "data"


def _load(name: str) -> bytes:
    return (DATA_DIR / name).read_bytes()


@pytest.fixture(scope="session")
def clean_source() -> bytes:
    return _load("clean_module.py.txt")


@pytest.fixture(scope="session")
def dirty_source() -> bytes:
    return _load("dirty_module.py.txt")


@pytest.fixture
def clean_file(clean_source) -> HashableFile:
    # content is preloaded so that benchmarks measure parsing and analysis
    # rather than disk IO
    return HashableFile(filename="clean_module.py", _binary_content=clean_source)


@pytest.fixture
def dirty_file(dirty_source) -> HashableFile:
    return HashableFile(filename="dirty_module.py", _binary_content=dirty_source)


@pytest.fixture(autouse=True)
def _reset_checker_state() -> None:
    # the checker visitors accumulate errors globally; reset between benchmarks
    # so that measurements do not depend on the ordering of the suite
    _clear_errors()
