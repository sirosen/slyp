from __future__ import annotations

import multiprocessing
import os
import queue
import sys
import types
import typing as t

from slyp.models import Message, Result

from ._worker import SlypWorker

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

# how long to wait on the result queue before checking that the workers are still alive
_POLL_INTERVAL = 0.1
# once every worker has exited with work outstanding, how long to keep reading results
# which may still be in flight before declaring them lost
_SHUTDOWN_GRACE_PERIOD = 1.0


class WorkerPool:
    """
    Runs a ``Worker`` in several processes, fed from a shared queue of filenames.

    Workers pull from one shared queue rather than each being handed a fixed share of
    the work, so a worker which draws slow files does not leave the others idle.
    """

    def __init__(
        self,
        mp_ctx: multiprocessing.context.BaseContext,
        worker: SlypWorker,
        num_workers: int | None = None,
    ) -> None:
        self.mp_ctx = mp_ctx
        self.worker = worker
        self.num_workers = num_workers or os.cpu_count() or 1

    def run(self, filenames: t.Iterable[str]) -> t.Iterator[Result]:
        """Process every filename, yielding results in completion order."""
        with _PoolRunResources(self.mp_ctx) as resources:
            resources.start_procs(self.num_workers, self.worker.run)
            num_tasks = resources.submit_work(filenames)

            yield from self._collect_results(
                resources.result_queue, num_tasks, resources.processes
            )

    def _collect_results(
        self,
        result_queue: multiprocessing.Queue[Result],
        num_tasks: int,
        processes: list[multiprocessing.Process],
    ) -> t.Iterator[Result]:
        remaining = num_tasks

        while remaining:
            try:
                result = result_queue.get(timeout=_POLL_INTERVAL)
            except queue.Empty:
                if any(process.is_alive() for process in processes):
                    continue

                # every worker has exited with work outstanding, meaning one died
                # without reporting. drain whatever is still in flight, then give up
                # rather than blocking forever
                try:
                    result = result_queue.get(timeout=_SHUTDOWN_GRACE_PERIOD)
                except queue.Empty:
                    yield Result(
                        success=False,
                        messages=[
                            Message(
                                f"slyp error: {remaining} file(s) were not processed "
                                "(a worker exited unexpectedly)"
                            )
                        ],
                    )
                    return

            remaining -= 1
            yield result


class _PoolRunResources:
    def __init__(self, mp_ctx: multiprocessing.context.BaseContext) -> None:
        self.mp_ctx = mp_ctx
        self.task_queue: multiprocessing.Queue[str | None] = self.mp_ctx.Queue()
        self.result_queue: multiprocessing.Queue[Result] = self.mp_ctx.Queue()
        self.processes: list[multiprocessing.Process] = []

    def start_procs(self, num_workers: int, target: t.Callable[..., t.Any]) -> None:
        # type ignore: BaseContext does not define Process, but all subtypes do
        self.processes.extend(
            # type ignore: BaseContext does not define Process, but all subtypes do
            self.mp_ctx.Process(  # type: ignore[attr-defined]
                target=target, args=(self.task_queue, self.result_queue)
            )
            for _ in range(num_workers)
        )
        for process in self.processes:
            process.start()

    def submit_work(self, work_items: t.Iterable[str]) -> int:
        num_tasks = 0
        for item in work_items:
            self.task_queue.put(item)
            num_tasks += 1

        for _ in self.processes:
            self.task_queue.put(None)

        return num_tasks

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> None:
        if exc_val:
            self._close_on_error()
        self._close()

    def _close_on_error(self) -> None:
        for process in self.processes:
            process.terminate()
        self.task_queue.cancel_join_thread()
        self.result_queue.cancel_join_thread()

    def _close(self) -> None:
        for process in self.processes:
            process.join()
