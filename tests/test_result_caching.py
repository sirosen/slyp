import os
import queue
import threading
from unittest import mock

import pytest

from slyp.checkers import _clear_errors as _clear_checker_errors
from slyp.checkers import check_file
from slyp.cli import main as cli_main
from slyp.fixer import fix_file


@pytest.fixture(autouse=True)
def _auto_clear_checker_errors():
    _clear_checker_errors()


@pytest.fixture
def in_tmp_path(tmp_path):
    old = os.getcwd()
    try:
        os.chdir(tmp_path)
        yield tmp_path
    finally:
        os.chdir(old)


class FakeProcess:
    """Run a worker in a thread rather than a process.

    Threads keep the queue blocking/sentinel behavior of the real workers, while
    leaving the worker in this interpreter so that patches on `slyp.driver` are
    visible to it.
    """

    def __init__(self, target, args) -> None:
        self._thread = threading.Thread(target=target, args=args)

    def start(self):
        self._thread.start()

    def join(self, timeout=None):
        self._thread.join(timeout)

    def is_alive(self):
        return self._thread.is_alive()


@pytest.fixture(autouse=True)
def _mock_parallel_processing():
    mock_manager = mock.MagicMock()
    mock_manager.__enter__.return_value = mock_manager
    mock_manager.Queue.return_value = queue.Queue()

    mock_mp_context = mock.Mock()
    mock_mp_context.Queue = queue.Queue
    mock_mp_context.Process = FakeProcess
    mock_mp_context.Manager.return_value = mock_manager

    with (
        mock.patch("multiprocessing.get_context", return_value=mock_mp_context),
        # one worker, so that the checker/fixer call counts are deterministic
        mock.patch("os.cpu_count", return_value=1),
    ):
        yield


@pytest.fixture
def run_cli(capsys):
    def _run_cli(args, assert_exit_code=0):
        retcode = 0
        try:
            cli_main(args)
        except SystemExit as e:
            retcode = e.code
        if assert_exit_code is not None:
            assert retcode == assert_exit_code
        return retcode

    return _run_cli


def test_cli_invocation_simple(run_cli, in_tmp_path, capsys):
    (in_tmp_path / "foo.py").write_text('x = "foo bar"\n')
    with (
        mock.patch(
            "slyp.executor._tasks.check_file", wraps=check_file
        ) as mock_check_file,
        mock.patch("slyp.executor._tasks.fix_file", wraps=fix_file) as mock_fix_file,
    ):
        assert run_cli(["foo.py"]) == 0, capsys.readouterr().out
        assert mock_check_file.call_count == 1
        assert mock_fix_file.call_count == 1


def test_double_cli_invocation_hits_cache(run_cli, in_tmp_path):
    (in_tmp_path / "foo.py").write_text('x = "foo bar"\n')
    with (
        mock.patch(
            "slyp.executor._tasks.check_file", wraps=check_file
        ) as mock_check_file,
        mock.patch("slyp.executor._tasks.fix_file", wraps=fix_file) as mock_fix_file,
    ):
        run_cli(["foo.py"])
        assert mock_check_file.call_count == 1
        assert mock_fix_file.call_count == 1

        # running again does not call the checkers or fixers again!
        run_cli(["foo.py"])
        assert mock_check_file.call_count == 1
        assert mock_fix_file.call_count == 1


@pytest.mark.parametrize("cache_on_first_run", (True, False))
def test_double_cli_invocation_skips_cache_with_no_cache_flag(
    run_cli, in_tmp_path, cache_on_first_run
):
    (in_tmp_path / "foo.py").write_text('x = "foo bar"\n')
    with (
        mock.patch(
            "slyp.executor._tasks.check_file", wraps=check_file
        ) as mock_check_file,
        mock.patch("slyp.executor._tasks.fix_file", wraps=fix_file) as mock_fix_file,
    ):
        run_cli(["foo.py"] if cache_on_first_run else ["--no-cache", "foo.py"])
        assert mock_check_file.call_count == 1
        assert mock_fix_file.call_count == 1

        # running again does all the work again
        run_cli(["--no-cache", "foo.py"])
        assert mock_check_file.call_count == 2
        assert mock_fix_file.call_count == 2


def test_cache_is_not_populated_under_no_cache(run_cli, in_tmp_path):
    (in_tmp_path / "foo.py").write_text('x = "foo bar"\n')
    with (
        mock.patch(
            "slyp.executor._tasks.check_file", wraps=check_file
        ) as mock_check_file,
        mock.patch("slyp.executor._tasks.fix_file", wraps=fix_file) as mock_fix_file,
    ):
        # setup: run with `--no-cache`, which should *not* populate the cache
        run_cli(["--no-cache", "foo.py"])
        assert mock_check_file.call_count == 1
        assert mock_fix_file.call_count == 1

        # now run without `--no-cache` and confirm that there was no cache hit
        run_cli(["foo.py"])
        assert mock_check_file.call_count == 2
        assert mock_fix_file.call_count == 2
