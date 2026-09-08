import pytest

from slyp.cli._parse import parse_args


def test_stdin_arg_is_invalid_with_other_files(capsys):
    with pytest.raises(SystemExit, match="2"):
        parse_args(["-", "foo.py"])

    _, err = capsys.readouterr()
    assert "stdin can only be used with one file at a time" in err


def test_stdin_arg_requires_only_flag(capsys):
    with pytest.raises(SystemExit, match="2"):
        parse_args(["-"])

    _, err = capsys.readouterr()
    assert "stdin mode requires '--only' to be set" in err


def test_use_git_ls_mutex_with_files(capsys):
    with pytest.raises(SystemExit, match="2"):
        parse_args(["foo.py", "--use-git-ls"])

    _, err = capsys.readouterr()
    assert "--use-git-ls requires no filenames as arguments" in err


def test_stdin_valid_usage():
    result = parse_args(["--only=fix", "-"])
    assert result.files == ["-"]


def test_list_flag_sets_mode():
    result = parse_args(["--list"])
    assert result.mode == "list_codes"
