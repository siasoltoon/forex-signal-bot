from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from config.settings import Settings
from .contracts import HEAVY_JOB_TYPES, JobRequest, JobResult
from .queue import QueueRecord, WorkerQueue

JobHandler = Callable[[dict[str, Any]], Any]


class WorkerDispatcher:
    """Queue-backed dispatcher for heavy worker jobs."""

    def __init__(self, submit: Callable[[JobRequest], Awaitable[JobResult]] | None = None, queue: WorkerQueue | None = None, recovery_grace_seconds: int = 30):
        self._submit = submit
        self._queue = queue
        self._active_submissions: set[asyncio.Task[Any]] = set()
        if recovery_grace_seconds < 0:
            raise ValueError("Recovery grace must not be negative")
        if self._queue is not None:
            self._queue.recover_expired_running(recovery_grace_seconds)

    @classmethod
    def from_settings(cls, submit: Callable[[JobRequest], Awaitable[JobResult]] | None = None, settings: Settings | None = None) -> "WorkerDispatcher":
        resolved = settings or Settings.load()
        queue = WorkerQueue(resolved.worker_queue_database_path)
        return cls(submit=submit, queue=queue, recovery_grace_seconds=resolved.worker_queue_recovery_grace_seconds)

    def enqueue_only(self, request: JobRequest) -> JobResult:
        if request.job_type not in HEAVY_JOB_TYPES:
            raise ValueError(f"Unsupported PC worker job type: {request.job_type}")
        if self._queue is None:
            return JobResult(request.job_id, "WORKER_OFFLINE", request.job_type, error="Worker queue is not configured")
        record = self._queue.enqueue(request)
        return JobResult(request.job_id, record.status, request.job_type, output=record.result or {}, error=record.error)

    def claim_next(self) -> QueueRecord | None:
        if self._queue is None:
            return None
        return self._queue.claim_next()

    def renew_remote_claim(self, job_id: str, claim_token: str) -> dict[str, Any]:
        if self._queue is None:
            raise RuntimeError("Worker queue is not configured")
        record = self._queue.renew_lease(job_id, claim_token)
        return {"job_id": record.job_id, "status": record.status}

    def apply_remote_result(self, result: JobResult, claim_token: str) -> dict[str, Any]:
        if self._queue is None:
            raise RuntimeError("Worker queue is not configured")
        if result.status == "COMPLETED":
            record = self._queue.finish(result.job_id, result=result.output, claim_token=claim_token)
        elif result.status == "FAILED":
            record = self._queue.fail(result.job_id, result.error or "Remote worker failed", claim_token=claim_token)
        elif result.status == "TIMEOUT":
            record = self._queue.timeout(result.job_id, result.error or "Remote worker timeout", claim_token=claim_token)
        elif result.status == "CANCELLED":
            record = self._queue.cancel(result.job_id, claim_token=claim_token)
        elif result.status == "WORKER_OFFLINE":
            record = self._queue.requeue(result.job_id, result.error or "Remote worker offline", claim_token=claim_token)
        else:
            raise ValueError(f"Unsupported remote terminal status: {result.status}")
        return {
            "job_id": record.job_id,
            "status": record.status,
            "job_type": record.job_type,
            "output": record.result or {},
            "error": record.error,
        }

    async def _renew_claim_lease(self, job_id: str, claim_token: str, timeout_seconds: int) -> None:
        if self._queue is None:
            return
        interval = min(30.0, max(1.0, float(timeout_seconds) / 3.0))
        try:
            while True:
                await asyncio.sleep(interval)
                record = self._queue.renew_lease(job_id, claim_token)
                if record.status != "RUNNING" or record.claim_token != claim_token:
                    return
        except asyncio.CancelledError:
            raise
        except Exception:
            return

    async def submit(self, request: JobRequest) -> JobResult:
        current_task = asyncio.current_task()
        if current_task is not None:
            self._active_submissions.add(current_task)
        try:
            return await self._submit_inner(request)
        finally:
            if current_task is not None:
                self._active_submissions.discard(current_task)

    async def _submit_inner(self, request: JobRequest) -> JobResult:
        if request.job_type not in HEAVY_JOB_TYPES:
            raise ValueError(f"Unsupported PC worker job type: {request.job_type}")
        if self._queue is None:
            if self._submit is None:
                return JobResult(request.job_id, "WORKER_OFFLINE", request.job_type, error="PC worker transport is not configured")
            return await self._submit(request)

        record = self._queue.enqueue(request)
        if record.status == "COMPLETED":
            return JobResult(request.job_id, "COMPLETED", request.job_type, output=record.result or {})
        if record.status in {"FAILED", "CANCELLED", "TIMEOUT"}:
            return JobResult(request.job_id, record.status, request.job_type, error=record.error)
        if record.status == "RUNNING":
            return JobResult(request.job_id, "RUNNING", request.job_type)

        claimed = self._queue.claim(request.job_id)
        if claimed is None:
            current = self._queue.get(request.job_id)
            return JobResult(request.job_id, current.status if current else "PENDING", request.job_type)

        claim_token = claimed.claim_token
        if self._submit is None:
            self._queue.fail(request.job_id, "PC worker transport is not configured", claim_token=claim_token)
            return JobResult(request.job_id, "WORKER_OFFLINE", request.job_type, error="PC worker transport is not configured")

        lease_task = asyncio.create_task(self._renew_claim_lease(request.job_id, claim_token, request.timeout_seconds))
        try:
            result = await self._submit(request)
        except asyncio.CancelledError:
            self._queue.cancel(request.job_id, claim_token=claim_token)
            raise
        except asyncio.TimeoutError as exc:
            self._queue.timeout(request.job_id, str(exc) or "Worker job timeout", claim_token=claim_token)
            raise
        except Exception as exc:
            self._queue.fail(request.job_id, str(exc), claim_token=claim_token)
            raise
        finally:
            lease_task.cancel()
            await asyncio.gather(lease_task, return_exceptions=True)

        if result.status == "COMPLETED":
            self._queue.finish(request.job_id, result=result.output, claim_token=claim_token)
        elif result.status == "WORKER_OFFLINE":
            self._queue.requeue(request.job_id, error=result.error or "PC worker offline", claim_token=claim_token)
        elif result.status == "TIMEOUT":
            self._queue.timeout(request.job_id, result.error or "Worker job timeout", claim_token=claim_token)
        elif result.status == "CANCELLED":
            self._queue.cancel(request.job_id, claim_token=claim_token)
        elif result.status == "FAILED":
            self._queue.fail(request.job_id, result.error or "Worker job failed", claim_token=claim_token)
        return result

    async def dispatch_pending(self, limit: int = 4) -> int:
        if self._queue is None or self._submit is None:
            return 0
        if limit < 1:
            raise ValueError("Pending dispatch limit must be positive")
        records = self._queue.pending(limit)
        scheduled = 0
        for record in records:
            request = JobRequest(
                job_id=record.job_id,
                job_type=record.job_type,
                payload=record.payload,
                priority=record.priority,
                timeout_seconds=record.timeout_seconds,
                allow_cpu_fallback=record.allow_cpu_fallback,
            )
            task = asyncio.create_task(self.submit(request))
            self._active_submissions.add(task)
            task.add_done_callback(self._active_submissions.discard)
            scheduled += 1
        return scheduled

    async def close_async(self, timeout_seconds: float = 10.0) -> None:
        if timeout_seconds <= 0:
            raise ValueError("Shutdown timeout must be greater than zero")
        active = [task for task in self._active_submissions if not task.done()]
        if active:
            _, pending = await asyncio.wait(active, timeout=timeout_seconds)
            for task in pending:
                task.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
        self.close()

    def close(self) -> None:
        if self._queue is not None:
            self._queue.close()
            self._queue = None

    def health(self) -> dict[str, Any]:
        if self._queue is None:
            return {"queue_configured": False}
        return {"queue_configured": True, "queue": self._queue.metrics()}

    async def submit_many(self, requests: list[JobRequest]) -> list[JobResult]:
        return await asyncio.gather(*(self.submit(request) for request in requests))


__all__ = ["WorkerDispatcher"]
