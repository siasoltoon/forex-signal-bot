from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from time import monotonic

from jobs.contracts import Job, JobStatus
from workers.contracts import JobResult


Handler = Callable[[Job], tuple[tuple[str, str], ...]]


class WorkerExecutor:
    def __init__(self, worker_id: str, handlers: dict[str, Handler]) -> None:
        self.worker_id = worker_id
        self.handlers = dict(handlers)

    def execute(self, job: Job) -> JobResult:
        handler = self.handlers.get(job.type)
        if handler is None:
            return JobResult(job.id, False, self.worker_id, error="unsupported_job_type")
        started = monotonic()
        try:
            output = handler(job)
            if monotonic() - started > job.timeout_seconds:
                return JobResult(job.id, False, self.worker_id, error="job_timeout")
            return JobResult(job.id, True, self.worker_id, output=output)
        except Exception as exc:
            return JobResult(job.id, False, self.worker_id, error=f"{type(exc).__name__}: {exc}")
