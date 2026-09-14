"""
Benchmark the per-file pipeline encoded into the executor's `process_file()`.
"""

import contextlib
import typing as t
from unittest import mock

import pytest

from slyp.executor._tasks import process_file
from slyp.hashable_file import HashableFile

from .corpus import MODULES


@contextlib.contextmanager
def _patch_file_io_operations(read_content: bytes) -> t.Iterator[None]:
    with (
        mock.patch.object(HashableFile, "_read") as mock_read,
        mock.patch.object(HashableFile, "_write"),
    ):
        mock_read.return_value = read_content
        yield


@pytest.mark.benchmark
@pytest.mark.parametrize(
    ("modname", "num_copies"),
    (
        # larger modules, run on one copy
        ("stdlib_textwrap", 1),
        ("stdlib_csv", 1),
        ("simple_cli_parser", 1),
        # small modules, run "many" times
        ("trivial", 1),
        ("trivial", 5),
        ("small", 1),
        ("small", 5),
    ),
)
def test_benchmark_process_files(benchmark, modname, num_copies):
    src = MODULES[modname]

    with _patch_file_io_operations(src):

        def _check():
            for i in range(num_copies):
                process_file(
                    f"/foo{i}.py",
                    mode="default",
                    disabled_codes=set(),
                    enabled_codes=set(),
                )

        benchmark(_check)
