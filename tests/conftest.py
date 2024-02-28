import textwrap

import pytest

from slyp.checkers import _clear_errors, check_file
from slyp.hashable_file import HashableFile


@pytest.fixture
def check_text(tmpdir):
    _clear_errors()

    def _check_text(
        text,
        *,
        verbose=False,
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
                verbose=verbose,
                disabled_codes=disabled_codes or set(),
                enabled_codes=enabled_codes or set(),
            )

    return _check_text
