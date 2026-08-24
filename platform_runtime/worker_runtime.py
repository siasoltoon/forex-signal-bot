from __future__ import annotations

import asyncio
import os
import platform
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4


class WorkerState(str, Enum):
    OFFLINE = "offline"
    IDLE = "idle"
    BUSY = "busy"
    DRAINING = "draining"


@dataclass(frozen=True)
class WorkerInfo:
    worker_id: str
    state: WorkerState
    cpu_percent: float
    memory_percent: float
    gpu_percent: float | None
    current_job: str | None
    heartbeat_at: datetime


@dataclass
class WorkerJob:
    job_id: str
    job_type: str
    priority: int
    payload: Mapping[str, Any]
    created_at: datetime
    retries: int = 0
    status: str = "queued"
    result: Mapping[str, Any] | None = None
    error: str | None = None

    @classmethod
    def create(cls, job_type: str, payload: Mapping[str, Any], priority: int = 100) -> "WorkerJob":
        return cls(uuid4().hex, job_type, priority, payload, datetime.now(timezone.utc))


class WorkerRegistry:
    def __init__(self) -> None:
        self._workers: dict[str, WorkerInfo] = {}

    def heartbeat(self, info: WorkerInfo) -> None:
        self._workers[info.worker_id] = info

    def get(self, worker_id: str) -> WorkerInfo | None:
        return self._workers.get(worker_id)

    def healthy(self, max_age_seconds: int = 60) -> tuple[WorkerInfo, ...]:
        now = datetime.now(timezone.utc)
        return tuple(w for w in self._workers.values() if (now - w.heartbeat_at).total_seconds() <= max_age_seconds and w.state != WorkerState.OFFLINE)

    def snapshot(self) -> tuple[WorkerInfo, ...]:
        return tuple(self._workers.values())


class JobQueue:
    def __init__(self) -> None:
        self._queue: asyncio.PriorityQueue[tuple[int, float, WorkerJob]] = asyncio.PriorityQueue()
        self._jobs: dict[str, WorkerJob] = {}

    async def submit(self, job: WorkerJob) -> str:
        self._jobs[job.job_id] = job
        await self._queue.put((job.priority, job.created_at.timestamp(), job))
        return job.job_id

    async def claim(self) -> WorkerJob:
        _, _, job = await self._queue.get()
        job.status = "running"
        return job

    def complete(self, job_id: str, result: Mapping[str, Any]) -> None:
        job = self._jobs[job_id]
        job.status = "succeeded"
        job.result = result

    def fail(self, job_id: str, error: Exception, retry: bool = True) -> None:
        job = self._jobs[job_id]
        job.retries += 1
        job.error = f"{type(error).__name__}: {error}"
        job.status = "queued" if retry else "failed"

    def get(self, job_id: str) -> WorkerJob | None:
        return self._jobs.get(job_id)


def local_worker_id() -> str:
    return f"{platform.node()}:{os.getpid()}"
