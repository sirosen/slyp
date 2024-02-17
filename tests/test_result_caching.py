import os
from unittest import mock

import pytest

from slyp.checkers import _clear_errors as _clear_checker_errors
from slyp.cli import check_file, fix_file
from slyp.cli import main as cli_main


@pytest.fixture(autouse=True)
def _auto_clear_checker_errors():
    _clear_checker_errors()


@pytest.fixture
def run_cli(capsys):
    def _run_cli(args, assert_exit_code=0):
        with mock.patch("sys.argv", ["slyp"] + args):
            retcode = 0
            try:
                cli_main()
            except SystemExit as e:
                retcode = e.code
            if assert_exit_code is not None:
                assert retcode == assert_exit_code
            return retcode

    return _run_cli


def test_cli_invocation_simple(run_cli, tmpdir, capsys):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write('x = "foo bar"\n')
    with mock.patch(
        "slyp.cli.check_file", wraps=check_file
    ) as mock_check_file, mock.patch(
        "slyp.cli.fix_file", wraps=fix_file
    ) as mock_fix_file:
        assert run_cli(["foo.py"]) == 0, capsys.readouterr().out
        assert mock_check_file.call_count == 1
        assert mock_fix_file.call_count == 1


def test_double_cli_invocation_hits_cache(run_cli, tmpdir):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write('x = "foo bar"\n')
    with mock.patch(
        "slyp.cli.check_file", wraps=check_file
    ) as mock_check_file, mock.patch(
        "slyp.cli.fix_file", wraps=fix_file
    ) as mock_fix_file:
        run_cli(["foo.py"])
        assert mock_check_file.call_count == 1
        assert mock_fix_file.call_count == 1

        # running again does not call the checkers or fixers again!
        run_cli(["foo.py"])
        assert mock_check_file.call_count == 1
        assert mock_fix_file.call_count == 1


@pytest.mark.parametrize("cache_on_first_run", (True, False))
def test_double_cli_invocation_skips_cache_with_no_cache_flag(
    run_cli, tmpdir, cache_on_first_run
):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write('x = "foo bar"\n')
    with mock.patch(
        "slyp.cli.check_file", wraps=check_file
    ) as mock_check_file, mock.patch(
        "slyp.cli.fix_file", wraps=fix_file
    ) as mock_fix_file:
        run_cli(["foo.py"] if cache_on_first_run else ["--no-cache", "foo.py"])
        assert mock_check_file.call_count == 1
        assert mock_fix_file.call_count == 1

        # running again does all the work again
        run_cli(["--no-cache", "foo.py"])
        assert mock_check_file.call_count == 2
        assert mock_fix_file.call_count == 2


def test_cache_is_not_populated_under_no_cache(run_cli, tmpdir):
    os.chdir(tmpdir)
    tmpdir.join("foo.py").write('x = "foo bar"\n')
    with mock.patch(
        "slyp.cli.check_file", wraps=check_file
    ) as mock_check_file, mock.patch(
        "slyp.cli.fix_file", wraps=fix_file
    ) as mock_fix_file:
        # setup: run with `--no-cache`, which should *not* populate the cache
        run_cli(["--no-cache", "foo.py"])
        assert mock_check_file.call_count == 1
        assert mock_fix_file.call_count == 1

        # now run without `--no-cache` and confirm that there was no cache hit
        run_cli(["foo.py"])
        assert mock_check_file.call_count == 2
        assert mock_fix_file.call_count == 2
