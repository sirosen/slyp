from __future__ import annotations

import multiprocessing
import multiprocessing.context
import multiprocessing.process
import os
import queue
import typing as t

from slyp.result import Message, Result

from ._worker import SlypWorker

# how long to wait on the result queue before checking that the workers are still alive
_POLL_INTERVAL = 0.1
# once every worker has exited with work outstanding, how long to keep reading results
# which may still be in flight before declaring them lost
_SHUTDOWN_GRACE_PERIOD = 1.0


class WorkerPool:
    """Runs a ``Worker`` in several processes, fed from a shared queue of filenames.

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
        task_queue: multiprocessing.Queue[str | None] = self.mp_ctx.Queue()
        result_queue: multiprocessing.Queue[Result] = self.mp_ctx.Queue()

        # each worker gets its own copy of `self.worker`, whose `initialize` then runs
        # in that process -- so per-worker resources are never shared between them
        processes = [
            self.mp_ctx.Process(target=self.worker.run, args=(task_queue, result_queue))
            for _ in range(self.num_workers)
        ]
        for process in processes:
            process.start()

        try:
            num_tasks = 0
            for filename in filenames:
                task_queue.put(filename)
                num_tasks += 1

            for _ in processes:
                task_queue.put(None)

            yield from self._collect_results(result_queue, num_tasks, processes)
        finally:
            for process in processes:
                process.join()

    def _collect_results(
        self,
        result_queue: multiprocessing.Queue[Result],
        num_tasks: int,
        processes: list[multiprocessing.process.BaseProcess],
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
