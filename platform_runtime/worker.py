from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class Job:
    type: str
    payload: dict
    priority: int = 0
    id: str = field(default_factory=lambda: str(uuid4()))
    status: JobStatus = JobStatus.QUEUED
    retry_count: int = 0
    worker_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: dict | None = None


class JobQueue:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def submit(self, job: Job) -> str:
        self._jobs[job.id] = job
        return job.id

    def claim(self, worker_id: str) -> Job | None:
        candidates = [job for job in self._jobs.values() if job.status in {JobStatus.QUEUED, JobStatus.RETRY}]
        if not candidates:
            return None
        job = max(candidates, key=lambda item: (item.priority, item.created_at))
        job.status = JobStatus.RUNNING
        job.worker_id = worker_id
        job.started_at = datetime.now(timezone.utc)
        return job

    def complete(self, job_id: str, result: dict) -> None:
        job = self._jobs[job_id]
        job.status = JobStatus.SUCCEEDED
        job.result = result
        job.finished_at = datetime.now(timezone.utc)

    def fail(self, job_id: str, retry: bool = True) -> None:
        job = self._jobs[job_id]
        job.retry_count += 1
        job.status = JobStatus.RETRY if retry else JobStatus.FAILED
        job.finished_at = datetime.now(timezone.utc)


@dataclass(frozen=True)
class WorkerHeartbeat:
    worker_id: str
    online: bool
    busy: bool
    cpu_percent: float = 0.0
    ram_percent: float = 0.0
    gpu_percent: float = 0.0
    current_job: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class WorkerRegistry:
    def __init__(self) -> None:
        self._workers: dict[str, WorkerHeartbeat] = {}

    def heartbeat(self, heartbeat: WorkerHeartbeat) -> None:
        self._workers[heartbeat.worker_id] = heartbeat

    def available(self) -> tuple[WorkerHeartbeat, ...]:
        return tuple(item for item in self._workers.values() if item.online and not item.busy)
