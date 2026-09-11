from __future__ import annotations

import dataclasses
import glob
import hashlib
import json
import multiprocessing
import os
import stat
import subprocess
import sys
import typing as t

from slyp.checkers import check_file
from slyp.codes import CODE_MAP
from slyp.constants import CONTRACT_VERSION, ValidMode
from slyp.executor import SlypWorker, WorkerPool
from slyp.fixer import fix_file
from slyp.hashable_file import HashableFile
from slyp.result import Result
from slyp.sqlite_cache import (
    CacheInitializer,
    MultiprocessCacheManager,
    NullCacheManagerShim,
)


@dataclasses.dataclass(slots=True)
class SlypArgs:
    """Fully normalized arguments, as parsed from the CLI."""

    mode: ValidMode
    verbosity: int
    use_git_ls: bool
    disabled_codes: set[str]
    enabled_codes: set[str]
    no_cache: bool
    files: t.Sequence[str]


def driver_main(args: SlypArgs) -> bool:
    if args.files == ["-"]:
        return process_stdin(args)
    else:
        return parallel_process(args)


def process_stdin(args: SlypArgs) -> bool:
    result = Result(success=True, messages=[])
    file_obj = HashableFile("-")

    match args.mode:
        case "fix":
            result = fix_file(file_obj)
            message_stream = sys.stderr
        case "lint":
            result = result.join(
                check_file(
                    file_obj,
                    disabled_codes=args.disabled_codes,
                    enabled_codes=args.enabled_codes,
                )
            )
            message_stream = sys.stdout
        # parsing + validation should protect us from ever reaching this
        case "list_codes" | "default":
            raise NotImplementedError(
                "stdin without --only value; should be unreachable"
            )
        case _ as unreachable:
            t.assert_never(unreachable)

    for message in result.messages:
        if message.verbosity <= args.verbosity:
            print(message.message, file=message_stream)

    return result.success


def parallel_process(args: SlypArgs) -> bool:
    if args.no_cache:
        return _run_workers(args, NullCacheManagerShim())
    else:
        cache_initializer = CacheInitializer()
        cache_initializer.ensure_db_exists()
        signature = compute_evaluation_signature(CONTRACT_VERSION, args)

        cache_manager = MultiprocessCacheManager(cache_initializer, signature)
        return _run_workers(args, cache_manager)


def _run_workers(
    args: SlypArgs, cache_manager: MultiprocessCacheManager | NullCacheManagerShim
) -> bool:
    mp_ctx = multiprocessing.get_context("fork")
    success = True

    with cache_manager.active_context(mp_ctx) as cache_context:
        pool = WorkerPool(
            mp_ctx,
            SlypWorker(
                args.mode,
                args.disabled_codes,
                args.enabled_codes,
                cache_manager.reader_factory,
                cache_context.make_write_handle(),
            ),
        )

        for result in pool.run(_announced_filenames(args)):
            for message in result.messages:
                if message.verbosity <= args.verbosity:
                    print(message.message)

            success = success and result.success

    return success


def _announced_filenames(args: SlypArgs) -> t.Iterator[str]:
    for filename in all_py_filenames(args.files, args.use_git_ls):
        if args.verbosity >= 1:
            print(f"slpy: processing {filename}", file=sys.stderr)
        yield filename


def compute_config_id(args: SlypArgs) -> str:
    # now we get the codes which are defined, convert to a string
    all_codes: str = json.dumps(sorted(CODE_MAP.keys()))
    # get the enabled/disabled codes, and make that a string
    code_opts = json.dumps(
        {
            "disabled": sorted(args.enabled_codes),
            "enabled": sorted(args.disabled_codes),
        }
    )

    config_hash = hashlib.sha256()
    config_hash.update(all_codes.encode())
    config_hash.update(code_opts.encode())

    # full ID is the base + the computed bits hashed
    return config_hash.hexdigest()


def compute_evaluation_signature(contract_version: str, args: SlypArgs) -> str:
    return f"contract:{contract_version}/config_id:{compute_config_id(args)}"


def all_py_filenames(files: t.Sequence[str], use_git_ls: bool) -> t.Iterable[str]:
    if files:
        yield from files
    elif use_git_ls:
        git_ls_files_proc = subprocess.run(
            ["git", "ls-files"], check=True, capture_output=True, text=True
        )
        candidates = git_ls_files_proc.stdout.split("\n")
        for file in candidates:
            if file == "":
                continue
            if is_python(file):
                yield file
    else:
        yield from glob.glob("**/*.py", recursive=True)


def is_python(filename: str) -> bool:
    # don't pay attention to symlinks or other special filetypes
    # those aren't really files to check
    # but you might be fed them by `git ls-files`
    if not stat.S_ISREG(os.lstat(filename).st_mode):
        return False

    # .py is good
    if filename.endswith(".py"):
        return True

    # if it's not executable, it couldn't be a script
    if not os.access(filename, os.X_OK):
        return False

    # but otherwise, look for a shebang which contains 'python' as a substring
    try:
        with open(filename, encoding="utf-8") as fp:
            firstline = fp.readline()
    except UnicodeDecodeError:
        return False
    if firstline.startswith("#!") and "python" in firstline:
        return True

    return False
