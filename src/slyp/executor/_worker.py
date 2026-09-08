from __future__ import annotations

import multiprocessing
import multiprocessing.context
import multiprocessing.process

from slyp.constants import ValidMode
from slyp.result import Message, Result
from slyp.sqlite_cache import (
    CacheReaderFactory,
    FileCacheReader,
    MultiprocessWriteHandle,
)

from ._tasks import process_file


class SlypWorker:
    """
    Workers represent subprocess executions. One worker is created per subproc.
    """

    def __init__(
        self,
        mode: ValidMode,
        disabled_codes: set[str],
        enabled_codes: set[str],
        reader_factory: CacheReaderFactory | None,
        cache_writer: MultiprocessWriteHandle | None,
    ) -> None:
        self.mode = mode
        self.disabled_codes = disabled_codes
        self.enabled_codes = enabled_codes
        self.reader_factory = reader_factory
        self.cache_writer = cache_writer
        self.cache_reader: FileCacheReader | None = None

    def initialize(self) -> None:
        # one cache reader, held for this worker's whole lifetime. opening a connection
        # costs considerably more than the lookup it serves, so it must not happen on
        # the per-file path
        if self.reader_factory is not None:
            self.cache_reader = self.reader_factory.make_reader()

    def shutdown(self) -> None:
        if self.cache_reader is not None:
            self.cache_reader.close()

    def handle_file(self, filename: str) -> Result:
        return process_file(
            filename,
            self.mode,
            self.disabled_codes,
            self.enabled_codes,
            self.cache_reader,
            self.cache_writer,
        )

    def run(
        self,
        task_queue: multiprocessing.Queue[str | None],
        result_queue: multiprocessing.Queue[Result],
    ) -> None:
        self.initialize()
        try:
            while True:
                filename = task_queue.get()
                # `None` is the stop signal, one of which is sent per worker
                if filename is None:
                    return
                result_queue.put(self._handle_file_capturing_errors(filename))
        finally:
            self.shutdown()

    def _handle_file_capturing_errors(self, filename: str) -> Result:
        # a failure on one file must not take the worker down with it
        try:
            return self.handle_file(filename)
        except Exception as e:
            return Result(
                success=False,
                messages=[
                    Message(f"slyp error on '{filename}': {e}"),
                    Message(
                        f"slyp error on '{filename}': {e.__traceback__}",
                        verbosity=2,
                    ),
                ],
            )
