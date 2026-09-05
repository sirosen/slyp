import pytest

from slyp.checkers import check_file
from slyp.hashable_file import HashableFile


@pytest.fixture
def corpus_filename(tmp_path):
    return tmp_path / "corpus.py"


@pytest.mark.benchmark
def test_benchmark_check(benchmark, corpus_filename, stdlib_module_source):
    def _check():
        return check_file(
            HashableFile(str(corpus_filename), _binary_content=stdlib_module_source),
            disabled_codes=set(),
            enabled_codes=set(),
        )

    benchmark(_check)
