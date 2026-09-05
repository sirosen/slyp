from __future__ import annotations

import sqlite3
import types
import typing as t

from ..hashable_file import HashableFile
from ._initializer import CacheInitializer


class FileCacheReader:
    def __init__(self, conn: sqlite3.Connection, signature: str) -> None:
        self.conn = conn
        self.signature = signature

    def contains_file(self, file: HashableFile) -> bool:
        cursor = self.conn.execute(
            (
                "SELECT COUNT(*) FROM passing_file_hashes "
                "WHERE file_content_sha=? AND evaluation_signature=?"
            ),
            (file.sha, self.signature),
        )
        result = cursor.fetchone()[0]
        cursor.close()
        return result != 0  # type: ignore[no-any-return]

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> t.Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> None:
        self.close()


class CacheReaderFactory:
    def __init__(
        self, initializer: CacheInitializer, evaluation_signature: str
    ) -> None:
        self.initializer = initializer
        self.signature = evaluation_signature

    def make_reader(self) -> FileCacheReader:
        conn = self.initializer.create_reader_connection()
        return FileCacheReader(conn, self.signature)

    @staticmethod
    def agnostic_contains_file(
        file: HashableFile, reader: FileCacheReader | CacheReaderFactory
    ) -> bool:
        """Check either reader type. If one is created via a factory, also close it."""
        if isinstance(reader, FileCacheReader):
            return reader.contains_file(file)
        with reader.make_reader() as ephemeral_reader:
            return ephemeral_reader.contains_file(file)
