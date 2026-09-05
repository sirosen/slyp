from __future__ import annotations

import pytest

from slyp.checkers import check_file
from slyp.checkers.abstract import run_ast_checkers
from slyp.checkers.concrete import run_cst_checkers


@pytest.mark.benchmark
def test_check_file_clean(benchmark, clean_file):
    result = benchmark(
        lambda: check_file(clean_file, disabled_codes=set(), enabled_codes=set())
    )

    assert result.success


@pytest.mark.benchmark
def test_check_file_with_findings(benchmark, dirty_file):
    result = benchmark(
        lambda: check_file(dirty_file, disabled_codes=set(), enabled_codes=set())
    )

    assert not result.success


@pytest.mark.benchmark
def test_check_file_all_codes_enabled(benchmark, dirty_file):
    result = benchmark(
        lambda: check_file(dirty_file, disabled_codes=set(), enabled_codes={"all"})
    )

    assert not result.success


@pytest.mark.benchmark
def test_run_cst_checkers(benchmark, dirty_file):
    errors = benchmark(lambda: run_cst_checkers(dirty_file))

    assert errors


@pytest.mark.benchmark
def test_run_ast_checkers(benchmark, dirty_file):
    errors = benchmark(lambda: run_ast_checkers(dirty_file))

    assert errors
