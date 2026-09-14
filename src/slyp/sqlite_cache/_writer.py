import sqlite3
import sys
import types

from ._initializer import CacheInitializer

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

_BATCH_SIZE: int = 100


class FileCacheWriter:
    def __init__(self, conn: sqlite3.Connection, signature: str) -> None:
        self.conn = conn
        self.signature = signature
        self._pending: list[str] = []

    def add_sha(self, sha: str) -> None:
        self._pending.append(sha)
        if len(self._pending) >= _BATCH_SIZE:
            self.flush()

    def flush(self) -> None:
        if not self._pending:
            return
        cursor = self.conn.executemany(
            "INSERT OR IGNORE INTO passing_file_hashes VALUES (?, ?)",
            [(sha, self.signature) for sha in self._pending],
        )
        cursor.close()
        self.conn.commit()
        self._pending.clear()

    def close(self) -> None:
        self.flush()
        self.conn.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> None:
        self.close()


class CacheWriterFactory:
    def __init__(
        self, initializer: CacheInitializer, evaluation_signature: str
    ) -> None:
        self.initializer = initializer
        self.signature = evaluation_signature

    def make_writer(self) -> FileCacheWriter:
        conn = self.initializer.create_writer_connection()
        return FileCacheWriter(conn, self.signature)
