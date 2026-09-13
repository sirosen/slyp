import sqlite3
import sys
import types

from ._initializer import CacheInitializer

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

_COMMIT_BATCH_SIZE: int = 100


class FileCacheWriter:
    def __init__(self, conn: sqlite3.Connection, signature: str) -> None:
        self.conn = conn
        self.signature = signature
        self._batch_counter: int = 0

    def add_sha(self, sha: str) -> None:
        # no commit here -- the inserts accumulate in a single transaction which is
        # committed on close, rather than paying a commit per file
        cursor = self.conn.execute(
            "INSERT OR IGNORE INTO passing_file_hashes VALUES (?, ?)",
            (sha, self.signature),
        )
        cursor.close()
        self._incr_or_commit()

    def _incr_or_commit(self) -> None:
        self._batch_counter += 1
        if self._batch_counter >= _COMMIT_BATCH_SIZE:
            self._batch_counter = 0
            self.conn.commit()

    def close(self) -> None:
        self.conn.commit()
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
