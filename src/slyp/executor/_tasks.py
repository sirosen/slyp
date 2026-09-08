from __future__ import annotations

from slyp.checkers import check_file
from slyp.constants import ValidMode
from slyp.fixer import fix_file
from slyp.hashable_file import HashableFile
from slyp.result import Message, Result
from slyp.sqlite_cache import (
    FileCacheReader,
    FileCacheWriter,
    MultiprocessWriteHandle,
)


def process_file(
    filename: str,
    mode: ValidMode,
    disabled_codes: set[str],
    enabled_codes: set[str],
    cache_reader: FileCacheReader | None = None,
    cache_writer: FileCacheWriter | MultiprocessWriteHandle | None = None,
) -> Result:
    result = Result(success=True, messages=[])
    file_obj = HashableFile(filename)

    if cache_reader is not None:
        if cache_reader.contains_file(file_obj):
            result.messages.append(
                Message(message=f"cache hit: {filename}", verbosity=2)
            )
            return result

    if mode in ("fix", "default"):
        result = result.join(fix_file(file_obj))
    if mode in ("lint", "default"):
        result = result.join(
            check_file(
                file_obj, disabled_codes=disabled_codes, enabled_codes=enabled_codes
            )
        )

    # results are only cached in the default mode because the mode is not
    # part of the signature (unclear whether or not it should be)
    if cache_writer and result.success and mode == "default":
        cache_writer.write(file_obj)
    return result
