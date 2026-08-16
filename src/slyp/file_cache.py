from __future__ import annotations

import contextlib
import copy
import multiprocessing
import pathlib
import shutil
import sqlite3
import textwrap
import threading
import typing as t

from slyp.hashable_file import HashableFile

_CACHEDIR = ".slyp_cache"


def _ensure_cachedir(cache_dir: pathlib.Path) -> None:
    cache_dir.mkdir(exist_ok=True)
    gitignore_path = cache_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text("*\n")


class PassingFileCache:
    def __init__(
        self,
        *,
        contract_version: str,
        config_id: str,
        cache_dir: pathlib.Path | None = None,
        db_name: str = "passing_files.db",
    ) -> None:
        self._cache_dir = cache_dir or pathlib.Path.cwd() / _CACHEDIR
        self._db_name = db_name

        self._config_id = config_id
        self._evaluation_signature = (
            f"contract:{contract_version}/config_id:{config_id}"
        )
        _ensure_cachedir(self._cache_dir)

        self._connection = self._connect()

    def _connect(self) -> sqlite3.Connection:
        return _connect_and_init(self._cache_dir / self._db_name)

    def connect(self) -> None:
        self._connection = self._connect()

    def close(self) -> None:
        self._connection.close()

    def clear(self) -> None:
        shutil.rmtree(self._cache_dir, ignore_errors=True)

    def __contains__(self, item: HashableFile) -> bool:
        cursor = self._connection.execute(
            (
                "SELECT COUNT(*) FROM passing_file_hashes "
                "WHERE file_content_sha=? AND evaluation_signature=?"
            ),
            (item.sha, self._evaluation_signature),
        )
        result = cursor.fetchone()[0]
        cursor.close()
        return result != 0

    def add(self, item: HashableFile) -> None:
        with self._suppress_unique_constraint_errors():
            cursor = self._connection.execute(
                "INSERT INTO passing_file_hashes VALUES (?, ?)",
                (item.sha, self._evaluation_signature),
            )
            cursor.close()

    def add_sha(self, sha: str) -> None:
        """like add(), but callers pass the sha directly"""
        with self._suppress_unique_constraint_errors():
            cursor = self._connection.execute(
                "INSERT INTO passing_file_hashes VALUES (?, ?)",
                (sha, self._evaluation_signature),
            )
            cursor.close()

    @contextlib.contextmanager
    def _suppress_unique_constraint_errors(self) -> t.Iterator[None]:
        try:
            yield
        except sqlite3.IntegrityError as e:
            if str(e).startswith("UNIQUE constraint failed"):
                return
            raise

    def __getstate__(self) -> dict[str, t.Any]:
        state = self.__dict__.copy()
        del state["_connection"]
        return state

    def __setstate__(self, state: dict[str, t.Any]) -> None:
        self.__dict__.update(state)
        self._connection = self._connect()


class FileCacheReadProxy:
    """A small shim interface for read-only access to the cache."""

    def __init__(self, cache: PassingFileCache) -> None:
        self.cache = cache

    def __contains__(self, item: HashableFile) -> bool:
        return item in self.cache


class MultiprocessCacheAddProxy:
    """
    A shim which provides a multiprocess queue for pushing writes into a central
    process, so that cache adds can be sent from subprocesses to the main process.
    """

    def __init__(self, cache: PassingFileCache) -> None:
        self.cache = cache
        self.queue: multiprocessing.Queue | None = None

    def make_cache_add_callback(self) -> t.Callable[[HashableFile], None]:
        return _QueueWriteCallback(self.queue)

    @contextlib.contextmanager
    def active(self) -> t.Iterator[None]:
        with multiprocessing.Manager() as manager:
            self.queue = manager.Queue()

            thread = threading.Thread(target=self._handle_writes)
            thread.start()

            yield

            self.queue.put(StopIteration())
            thread.join(15)
            self.queue = None

    def _handle_writes(self) -> None:
        # TODO: improve connection handling
        # we copy the cache object in order to create a fresh connection
        # but it would be better to not have a connection until we are ready to use it
        # or else to pass around a factory or "unbound" cache
        cache = copy.copy(self.cache)
        cache.close()
        cache.connect()
        while True:
            value = self.queue.get(block=True)
            if isinstance(value, str):
                cache.add_sha(value)
            elif isinstance(value, StopIteration):
                return
            else:
                raise NotImplementedError(value)


# standalone object to act as a closure
class _QueueWriteCallback:
    def __init__(self, queue: multiprocessing.Queue) -> None:
        self.queue = queue

    def __call__(self, item: HashableFile) -> None:
        self.queue.put(item.sha)


def _connect_and_init(filepath: pathlib.Path) -> sqlite3.Connection:
    if not filepath.exists():
        conn: sqlite3.Connection = sqlite3.connect(str(filepath))
        # currently, the tables are:
        # - file_hashes (the data we care about)
        # - slyp_db_metadata (config values, like schema versions)
        #
        # file_hashes has two columns, one for the content hash, and one for the
        # "evaluation signature" -- a string encoding any qualities of the checker, not
        # only the version, but also enabled/disabled flags
        conn.executescript(textwrap.dedent("""\
                CREATE TABLE passing_file_hashes (
                    file_content_sha VARCHAR NOT NULL,
                    evaluation_signature VARCHAR NOT NULL,
                    PRIMARY KEY (file_content_sha, evaluation_signature)
                );
                CREATE TABLE slyp_db_metadata (
                    attribute VARCHAR NOT NULL,
                    value VARCHAR NOT NULL,
                    PRIMARY KEY (attribute)
                );
                """))
        # mark the version which was used to create the DB
        # also mark the "database schema version" to handle graceful upgrades
        conn.executemany(
            "INSERT INTO slyp_db_metadata(attribute, value) VALUES (?, ?)",
            [("database_schema_version", "1")],
        )
        conn.commit()
    else:
        conn = sqlite3.connect(str(filepath))
    return conn
