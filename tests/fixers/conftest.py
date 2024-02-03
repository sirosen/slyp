import textwrap

import pytest

from slyp.fixer import fix_file


@pytest.fixture
def fix_text(tmpdir):
    def _fix_text(
        text, *, expect_changes=True, verbose=False, dedent=True, filename="X.py"
    ):
        handle = tmpdir.join(filename)
        text = textwrap.dedent(text) if dedent else text
        handle.write(text)
        with tmpdir.as_cwd():
            res = fix_file(filename, verbose=verbose)
            new_text = handle.read()

            if expect_changes:
                assert not res, "fixing made no changes"
            else:
                assert res, "fixing made changes"
                assert text == new_text

            return new_text

    return _fix_text
