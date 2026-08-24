from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from .contracts import HEAVY_JOB_TYPES, JobRequest, JobResult

JobHandler = Callable[[dict[str, Any]], Any]


class WorkerDispatcher:
    """Local dispatcher contract used by Railway to submit heavy work to a PC worker.

    The default implementation is deliberately transport-agnostic: deployment code can
    plug in HTTPS/WebSocket/queue transport without coupling analysis code to Telegram.
    """

    def __init__(self, submit: Callable[[JobRequest], Awaitable[JobResult]] | None = None):
        self._submit = submit

    async def submit(self, request: JobRequest) -> JobResult:
        if request.job_type not in HEAVY_JOB_TYPES:
            raise ValueError(f"Unsupported PC worker job type: {request.job_type}")
        if self._submit is None:
            return JobResult(request.job_id, "WORKER_OFFLINE", request.job_type, error="PC worker transport is not configured")
        return await self._submit(request)

    async def submit_many(self, requests: list[JobRequest]) -> list[JobResult]:
        return await asyncio.gather(*(self.submit(request) for request in requests))


__all__ = ["WorkerDispatcher"]
