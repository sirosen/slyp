import pytest

from slyp.cli._parse import parse_args


def test_stdin_arg_is_invalid_with_other_files(capsys):
    with pytest.raises(SystemExit, match="2"):
        parse_args(["slyp", "-", "foo.py"])

    _, err = capsys.readouterr()
    assert "stdin can only be used with one file at a time" in err
