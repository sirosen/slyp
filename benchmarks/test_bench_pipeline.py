from __future__ import annotations

import pytest

from slyp.checkers import check_file
from slyp.fixer import fix_file
from slyp.hashable_file import HashableFile


def _process(filename: str) -> bool:
    """The per-file work done by a slyp worker: fix, then lint."""
    file_obj = HashableFile(filename)
    fix_result = fix_file(file_obj)
    check_result = check_file(
        file_obj, disabled_codes={"W201", "W202", "W203"}, enabled_codes=set()
    )
    return fix_result.success and check_result.success


@pytest.mark.benchmark
def test_process_file_end_to_end(benchmark, tmp_path, clean_source, monkeypatch):
    """Full single-file pipeline, including reading the file from disk.

    The clean source is used so that no rewrite happens and every iteration
    performs the same amount of work.
    """
    (tmp_path / "clean_module.py").write_bytes(clean_source)
    monkeypatch.chdir(tmp_path)

    success = benchmark(lambda: _process("clean_module.py"))

    assert success


@pytest.mark.benchmark
def test_hashable_file_sha(benchmark, tmp_path, clean_source, monkeypatch):
    (tmp_path / "clean_module.py").write_bytes(clean_source)
    monkeypatch.chdir(tmp_path)

    sha = benchmark(lambda: HashableFile("clean_module.py").sha)

    assert len(sha) == 64
