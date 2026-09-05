import pytest

from slyp.fixer import _fix_data


@pytest.mark.benchmark
def test_benchmark_fix(benchmark, stdlib_module_source):
    benchmark(_fix_data, stdlib_module_source)
