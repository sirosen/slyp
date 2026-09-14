import pytest

from slyp.fixer import _fix_data

from .corpus import MODULES


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "module", ("stdlib_csv", "stdlib_textwrap", "trivial", "small", "simple_cli_parser")
)
def test_benchmark_fix(benchmark, module):
    data = MODULES[module]
    benchmark(_fix_data, data)
