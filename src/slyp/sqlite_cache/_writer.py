import contextlib
import sqlite3
import types
import typing as t

from ..hashable_file import HashableFile
from ._initializer import CacheInitializer


class FileCacheWriter:
    def __init__(self, conn: sqlite3.Connection, signature: str) -> None:
        self.conn = conn
        self.signature = signature

    def write(self, item: HashableFile) -> None:
        self.add_sha(item.sha)

    def add_sha(self, sha: str) -> None:
        with self._suppress_unique_constraint_errors():
            cursor = self.conn.execute(
                "INSERT INTO passing_file_hashes VALUES (?, ?)",
                (sha, self.signature),
            )
            cursor.close()
            self.conn.commit()

    @contextlib.contextmanager
    def _suppress_unique_constraint_errors(self) -> t.Iterator[None]:
        try:
            yield
        except sqlite3.IntegrityError as e:
            if str(e).startswith("UNIQUE constraint failed"):
                return
            raise

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


class CacheWriterFactory:
    def __init__(
        self, initializer: CacheInitializer, evaluation_signature: str
    ) -> None:
        self.initializer = initializer
        self.signature = evaluation_signature

    def make_writer(self) -> FileCacheWriter:
        conn = self.initializer.create_connection()
        return FileCacheWriter(conn, self.signature)
