import os

import pytest

from slyp.checkers import _clear_errors, check_file


@pytest.fixture(autouse=True)
def _auto_clear_errors():
    _clear_errors()


def test_check_captures_e100(tmpdir, capsys):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write(
        """\
x = "foo" "bar"
"""
    )
    check_file("foo.py", verbose=False, disabled_codes=set())

    assert "foo.py:1: unnecessary string concat (E100)" in capsys.readouterr().out
