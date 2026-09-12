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


@pytest.fixture
def corpus_filename(tmp_path):
    return tmp_path / "corpus.py"


@pytest.mark.benchmark
def test_benchmark_process_file(benchmark, corpus_filename):
    def _check():
        process_file(
            str(corpus_filename),
            mode="default",
            disabled_codes=set(),
            enabled_codes=set(),
        )

    benchmark(_check)
