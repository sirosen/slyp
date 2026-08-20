from __future__ import annotations

import contextlib
import functools
import multiprocessing
import threading
import typing as t

from ..hashable_file import HashableFile
from ._initializer import CacheInitializer
from ._reader import CacheReaderFactory
from ._writer import CacheWriterFactory


class MultiprocessWriteHandle:
    def __init__(self, queue: multiprocessing.Queue[str | StopIteration]) -> None:
        self.queue = queue

    def write(self, item: HashableFile) -> None:
        self.queue.put(item.sha)


class MultiprocessCacheContext:
    def __init__(
        self,
        manager: MultiprocessCacheManager,
        queue: multiprocessing.Queue[str | StopIteration],
    ) -> None:
        self.manager = manager
        self.queue = queue

    def make_write_handle(self) -> MultiprocessWriteHandle:
        return MultiprocessWriteHandle(self.queue)


class MultiprocessCacheManager:
    def __init__(self, initializer: CacheInitializer, signature: str) -> None:
        self.initializer = initializer
        self.signature = signature

    @functools.cached_property
    def writer_factory(self) -> CacheWriterFactory:
        return CacheWriterFactory(self.initializer, self.signature)

    @functools.cached_property
    def reader_factory(self) -> CacheReaderFactory:
        return CacheReaderFactory(self.initializer, self.signature)

    @contextlib.contextmanager
    def active_context(
        self, mp_ctx: multiprocessing.context.BaseContext
    ) -> t.Iterator[MultiprocessCacheContext]:
        with mp_ctx.Manager() as manager:
            queue: multiprocessing.Queue[str | StopIteration] = (
                manager.Queue()  # type: ignore[assignment]
            )
            thread = threading.Thread(target=self._handle_writes, args=(queue,))
            thread.start()

            yield MultiprocessCacheContext(self, queue)

            queue.put(StopIteration())
            thread.join(15)

    def _handle_writes(self, queue: multiprocessing.Queue[str | StopIteration]) -> None:
        with self.writer_factory.make_writer() as writer:
            while True:
                value = queue.get(block=True)
                if isinstance(value, str):
                    writer.add_sha(value)
                elif isinstance(value, StopIteration):
                    return
                else:
                    raise NotImplementedError(value)


class NullCacheManagerShim:
    def __init__(self) -> None:
        self.reader_factory = None

    def make_write_handle(self) -> None:
        return None

    @contextlib.contextmanager
    def active_context(
        self, mp_ctx: multiprocessing.context.BaseContext
    ) -> t.Iterator[t.Self]:
        yield self
