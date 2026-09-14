import pytest

from slyp.checkers import check_file
from slyp.hashable_file import HashableFile

from .corpus import MODULES


@pytest.fixture
def corpus_filename(tmp_path):
    return tmp_path / "corpus.py"


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "module", ("stdlib_csv", "stdlib_textwrap", "trivial", "small", "simple_cli_parser")
)
def test_benchmark_check(benchmark, corpus_filename, module):
    def _check():
        return check_file(
            HashableFile(str(corpus_filename), _binary_content=MODULES[module]),
            disabled_codes=set(),
            enabled_codes=set(),
        )

    benchmark(_check)
