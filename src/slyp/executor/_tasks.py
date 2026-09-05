from __future__ import annotations

from slyp.checkers import check_file
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
    only: str | None,
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

    if only in ("fix", None):
        result = result.join(fix_file(file_obj))
    if only in ("lint", None):
        result = result.join(
            check_file(
                file_obj, disabled_codes=disabled_codes, enabled_codes=enabled_codes
            )
        )

    if cache_writer and result.success and only is None:
        cache_writer.write(file_obj)
    return result
