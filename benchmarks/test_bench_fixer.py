from __future__ import annotations

import libcst
import pytest

from slyp.fixer import _find_disabled_ranges, _fix_data


@pytest.mark.benchmark
def test_fix_data_no_changes(benchmark, clean_source):
    fixed = benchmark(lambda: _fix_data(clean_source))

    assert fixed == clean_source


@pytest.mark.benchmark
def test_fix_data_with_changes(benchmark, dirty_source):
    fixed = benchmark(lambda: _fix_data(dirty_source))

    assert fixed != dirty_source


@pytest.mark.benchmark
def test_find_disabled_ranges(benchmark, dirty_source):
    ranges = benchmark(lambda: _find_disabled_ranges(dirty_source))

    assert ranges == []


@pytest.mark.benchmark
def test_libcst_parse_baseline(benchmark, dirty_source):
    """Baseline for the cost of building the CST which the fixer operates on."""
    tree = benchmark(lambda: libcst.parse_module(dirty_source))

    assert tree is not None
