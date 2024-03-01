import textwrap

import pytest

from slyp.checkers import _clear_errors, check_file
from slyp.fixer import fix_file
from slyp.hashable_file import HashableFile


@pytest.fixture
def check_text(tmpdir):
    _clear_errors()

    def _check_text(
        text,
        *,
        disabled_codes=None,
        enabled_codes=None,
        dedent=True,
        filename="X.py",
    ):
        handle = tmpdir.join(filename)
        text = textwrap.dedent(text) if dedent else text
        handle.write(text)

        with tmpdir.as_cwd():
            return check_file(
                HashableFile(filename),
                disabled_codes=disabled_codes or set(),
                enabled_codes=enabled_codes or set(),
            )

    return _check_text


@pytest.fixture
def fix_text(tmpdir):
    def _fix_text(text, *, expect_changes=True, dedent=True, filename="X.py"):
        handle = tmpdir.join(filename)
        text = textwrap.dedent(text) if dedent else text
        handle.write(text)

        with tmpdir.as_cwd():
            res = fix_file(HashableFile(filename))
            new_text = handle.read()

            if expect_changes:
                assert not res.success, "fixing made no changes"
            else:
                assert res.success, "fixing made changes"
                assert text == new_text

            return new_text, res

    return _fix_text
