"""
Benchmark the per-file pipeline encoded into the executor's `process_file()`.
"""

from unittest import mock

import pytest

from slyp.executor._tasks import process_file
from slyp.hashable_file import HashableFile


@pytest.fixture(autouse=True)
def _patch_file_io_operations(stdlib_module_source):
    with (
        mock.patch.object(HashableFile, "_read") as mock_read,
        mock.patch.object(HashableFile, "_write"),
    ):
        mock_read.return_value = stdlib_module_source
        yield


@pytest.mark.benchmark
@pytest.mark.parametrize("num_files", (1, 2, 5))
def test_benchmark_process_files(benchmark, num_files):
    def _check():
        for i in range(num_files):
            process_file(
                f"/foo{i}.py",
                mode="default",
                disabled_codes=set(),
                enabled_codes=set(),
            )

    benchmark(_check)
