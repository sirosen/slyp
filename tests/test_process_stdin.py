import inspect
import io
import sys
from unittest import mock

from slyp.driver import process_stdin

_BAD_SOURCE = """\
a = "foo\\\\ " r"bar\\."
"""


def test_fix_of_stdin_writes_to_stdout(capsys):
    mock_args = mock.Mock()
    mock_args.verbosity = 0
    mock_args.only = "fix"

    fake_stdin = mock.Mock()
    fake_stdin.buffer = io.BytesIO()
    # for fun, use the source of the current module as the fake stdin content
    mod = sys.modules[__name__]
    modsource = inspect.getsource(mod)
    fake_stdin.buffer.write(modsource.encode())
    fake_stdin.buffer.seek(0)

    with mock.patch.object(sys, "stdin", fake_stdin):
        process_stdin(mock_args, [], [])

    out, _err = capsys.readouterr()
    assert out == modsource


def test_lint_of_stdin_writes_to_stdout(capsys):
    mock_args = mock.Mock()
    mock_args.verbosity = 0
    mock_args.only = "lint"

    fake_stdin = mock.Mock()
    fake_stdin.buffer = io.BytesIO()
    fake_stdin.buffer.write(_BAD_SOURCE.encode())
    fake_stdin.buffer.seek(0)

    with mock.patch.object(sys, "stdin", fake_stdin):
        process_stdin(mock_args, [], [])

    out, _err = capsys.readouterr()
    assert "unnecessary string concat (E100)" in out
