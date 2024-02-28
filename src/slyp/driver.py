from __future__ import annotations

import argparse
import glob
import hashlib
import json
import multiprocessing.pool
import os
import stat
import subprocess
import typing as t

from slyp.checkers import check_file
from slyp.codes import CODE_MAP
from slyp.file_cache import PassingFileCache
from slyp.fixer import fix_file
from slyp.hashable_file import HashableFile
from slyp.result import Message, Result

DEFAULT_DISABLED_CODES: set[str] = {"W201", "W202", "W203"}


def driver_main(args: argparse.Namespace) -> bool:
    # parse inputs from comma delimited lists
    disabled_codes = {x for x in args.disable.split(",") if x != ""}
    enabled_codes = {x for x in args.enable.split(",") if x != ""}
    # add default disables if "all" is not in --enable
    if "all" not in enabled_codes:
        disabled_codes = disabled_codes | DEFAULT_DISABLED_CODES

    if not args.no_cache:
        passing_cache: PassingFileCache | None = PassingFileCache(
            contract_version="1.2",
            config_id=compute_config_id(enabled_codes, disabled_codes),
        )
    else:
        passing_cache = None

    process_pool = multiprocessing.pool.Pool()

    futures = []
    for filename in all_py_filenames(args.files, args.use_git_ls):
        futures.append(
            process_pool.apply_async(
                process_file,
                (filename, disabled_codes, enabled_codes, passing_cache),
            )
        )
    process_pool.close()
    process_pool.join()

    result = Result(success=True, messages=[])

    for future in futures:
        result = result.join(future.get())

    for message in sorted(result.messages):
        if message.verbosity <= args.verbosity:
            print(message.message)

    return result.success


def process_file(
    filename: str,
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

    fix_result = fix_file(file_obj)
    check_result = check_file(
        file_obj, disabled_codes=disabled_codes, enabled_codes=enabled_codes
    )

    result = result.join(fix_result).join(check_result)

    if passing_cache and result.success:
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
