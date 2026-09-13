from __future__ import annotations

import glob
import hashlib
import json
import multiprocessing
import os
import stat
import subprocess
import sys
import types
import typing as t

from slyp.checkers import check_file
from slyp.codes import CODE_MAP
from slyp.constants import CONTRACT_VERSION
from slyp.executor import SlypWorker, WorkerPool
from slyp.fixer import fix_file
from slyp.hashable_file import HashableFile
from slyp.models import Result, SlypRequest
from slyp.sqlite_cache import (
    CacheInitializer,
    CacheReaderFactory,
    CacheWriterFactory,
    FileCacheWriter,
)

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


def driver_main(args: SlypRequest) -> bool:
    if args.files == ["-"]:
        return process_stdin(args)
    else:
        return parallel_process(args)


def process_stdin(args: SlypRequest) -> bool:
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


def parallel_process(args: SlypRequest) -> bool:
    if args.no_cache:
        return _run_workers(args, None, None)
    else:
        cache_initializer = CacheInitializer()
        cache_initializer.ensure_db_exists()
        signature = compute_evaluation_signature(CONTRACT_VERSION, args)

        return _run_workers(
            args,
            CacheReaderFactory(cache_initializer, signature),
            CacheWriterFactory(cache_initializer, signature),
        )


def _run_workers(
    args: SlypRequest,
    reader_factory: CacheReaderFactory | None,
    writer_factory: CacheWriterFactory | None,
) -> bool:
    mp_ctx = multiprocessing.get_context("fork")
    success = True

    pool = WorkerPool(
        mp_ctx,
        SlypWorker(
            args.mode,
            args.disabled_codes,
            args.enabled_codes,
            reader_factory,
            writer_factory is not None,
        ),
    )

    with _ResultHandler(writer_factory, args.verbosity) as handler:
        for result in pool.run(_announced_filenames(args)):
            handler(result)
            success = success and result.success

    return success


class _ResultHandler:
    def __init__(
        self, writer_factory: CacheWriterFactory | None, verbosity: int
    ) -> None:
        self.writer_factory = writer_factory
        self.verbosity = verbosity
        self.writer: FileCacheWriter | None = None

    def __call__(self, result: Result) -> None:
        for message in result.messages:
            if message.verbosity <= self.verbosity:
                print(message.message)

        if (
            result.cache_write_sha is not None
            and (writer := self.get_writer()) is not None
        ):
            writer.add_sha(result.cache_write_sha)

    def get_writer(self) -> FileCacheWriter | None:
        if self.writer_factory is None:
            return None
        if self.writer is None:
            self.writer = self.writer_factory.make_writer()
        return self.writer

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> None:
        if self.writer is not None:
            self.writer.close()


def _announced_filenames(args: SlypRequest) -> t.Iterator[str]:
    for filename in all_py_filenames(args.files, args.use_git_ls):
        if args.verbosity >= 1:
            print(f"slpy: processing {filename}", file=sys.stderr)
        yield filename


def compute_config_id(args: SlypRequest) -> str:
    # now we get the codes which are defined, convert to a string
    all_codes: str = json.dumps(sorted(CODE_MAP.keys()))
    # get the enabled/disabled codes, and make that a string
    code_opts = json.dumps(
        {
            "disabled": sorted(args.disabled_codes),
            "enabled": sorted(args.enabled_codes),
        }
    )

    config_hash = hashlib.sha256()
    config_hash.update(all_codes.encode())
    config_hash.update(code_opts.encode())

    # full ID is the base + the computed bits hashed
    return config_hash.hexdigest()


def compute_evaluation_signature(contract_version: str, args: SlypRequest) -> str:
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
