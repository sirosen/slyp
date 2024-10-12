from __future__ import annotations

import argparse
import glob
import hashlib
import json
import multiprocessing.pool
import os
import stat
import subprocess
import time
import typing as t

from slyp.checkers import check_file
from slyp.codes import CODE_MAP
from slyp.file_cache import PassingFileCache
from slyp.fixer import fix_file
from slyp.hashable_file import HashableFile
from slyp.result import Message, Result

DEFAULT_DISABLED_CODES: set[str] = {"W201", "W202", "W203"}
CONTRACT_VERSION: str = "1.6"


def driver_main(args: argparse.Namespace) -> bool:
    # parse inputs from comma delimited lists
    disabled_codes = {x for x in args.disable.split(",") if x != ""}
    enabled_codes = {x for x in args.enable.split(",") if x != ""}
    # add default disables if "all" is not in --enable
    if "all" not in enabled_codes:
        disabled_codes = disabled_codes | DEFAULT_DISABLED_CODES

    if args.files == ["-"]:
        return process_stdin(args, disabled_codes, enabled_codes)
    else:
        return parallel_process(args, disabled_codes, enabled_codes)


def process_stdin(
    args: argparse.Namespace, disabled_codes: set[str], enabled_codes: set[str]
) -> bool:
    result = Result(success=True, messages=[])
    file_obj = HashableFile("-")

    if args.only == "fix":
        result = fix_file(file_obj)
    elif args.only == "lint":
        result = result.join(
            check_file(
                file_obj,
                disabled_codes=disabled_codes,
                enabled_codes=enabled_codes,
            )
        )
    else:
        raise NotImplementedError("stdin with unexpected --only value")

    for message in result.messages:
        if message.verbosity <= args.verbosity:
            print(message.message)

    return result.success


def parallel_process(
    args: argparse.Namespace, disabled_codes: set[str], enabled_codes: set[str]
) -> bool:
    if not args.no_cache:
        passing_cache: PassingFileCache | None = PassingFileCache(
            contract_version=CONTRACT_VERSION,
            config_id=compute_config_id(enabled_codes, disabled_codes),
        )
    else:
        passing_cache = None

    process_pool = multiprocessing.pool.Pool()

    futures = {}
    for filename in all_py_filenames(args.files, args.use_git_ls):
        if args.verbosity >= 1:
            print(f"slpy: processing {filename}")
        futures[filename] = process_pool.apply_async(
            process_file,
            (filename, args.only, disabled_codes, enabled_codes, passing_cache),
        )
    process_pool.close()

    success = True

    while futures:
        ready = set()
        for filename, future in futures.items():
            if future.ready():
                ready.add(filename)
        if not ready:
            time.sleep(0.05)

        for filename in ready:
            future = futures.pop(filename)
            try:
                result = future.get()
            except Exception as e:
                result = Result(
                    success=False,
                    messages=[
                        Message(f"slyp error on '{filename}': {e}"),
                        Message(
                            f"slyp error on '{filename}': {e.__traceback__}",
                            verbosity=2,
                        ),
                    ],
                )
            for message in result.messages:
                if message.verbosity <= args.verbosity:
                    print(message.message)

            success = success and result.success

    process_pool.join()

    return result.success


def process_file(
    filename: str,
    only: str | None,
    disabled_codes: set[str],
    enabled_codes: set[str],
    passing_cache: PassingFileCache | None,
) -> Result:
    result = Result(success=True, messages=[])
    file_obj = HashableFile(filename)

    if passing_cache:
        if file_obj in passing_cache:
            result.messages.append(
                Message(message=f"cache hit: {filename}", verbosity=2)
            )
            return result

    if only in ("fix", None):
        result = result.join(fix_file(file_obj))
    if only in ("lint", None):
        result = result.join(
            check_file(
                file_obj, disabled_codes=disabled_codes, enabled_codes=enabled_codes
            )
        )

    if passing_cache and result.success and only is None:
        passing_cache.add(file_obj)
    return result


def compute_config_id(enabled_codes: set[str], disabled_codes: set[str]) -> str:
    # now we get the codes which are defined, convert to a string
    all_codes: str = json.dumps(sorted(CODE_MAP.keys()))
    # get the enabled/disabled codes, and make that a string
    code_opts = json.dumps(
        {
            "disabled": sorted(enabled_codes),
            "enabled": sorted(disabled_codes),
        }
    )

    config_hash = hashlib.sha256()
    config_hash.update(all_codes.encode())
    config_hash.update(code_opts.encode())

    # full ID is the base + the computed bits hashed
    return config_hash.hexdigest()


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
