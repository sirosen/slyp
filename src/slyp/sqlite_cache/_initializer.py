from __future__ import annotations

import functools
import pathlib
import sqlite3
import textwrap

_CACHEDIR = ".slyp_cache"


class CacheInitializer:
    def __init__(
        self,
        cache_dir: pathlib.Path | None = None,
        db_name: str = "passing_files.db",
    ) -> None:
        self.cache_dir = cache_dir or self._default_cachedir()
        self.db_name = db_name

    def _default_cachedir(self) -> pathlib.Path:
        return pathlib.Path.cwd() / _CACHEDIR

    @functools.cached_property
    def filepath(self) -> pathlib.Path:
        return self.cache_dir / self.db_name

    def init_dir(self) -> None:
        self.cache_dir.mkdir(exist_ok=True)
        gitignore_path = self.cache_dir / ".gitignore"
        if not gitignore_path.exists():
            gitignore_path.write_text("*\n")

    def create_writer_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.filepath), autocommit=False)

    def create_reader_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.filepath))

    def ensure_db_exists(self) -> None:
        self.init_dir()
        if not self.filepath.exists():
            conn = self.create_writer_connection()
            try:
                self._provision_db(conn)
            finally:
                conn.close()

    def _provision_db(self, conn: sqlite3.Connection) -> None:
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
