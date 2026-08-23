from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class Job:
    job_id: str
    job_type: str
    priority: int = 0
    status: JobStatus = JobStatus.QUEUED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    finished_at: datetime | None = None
    worker_id: str | None = None
    retry_count: int = 0
    timeout_seconds: int = 300
    payload: dict[str, object] = field(default_factory=dict)
    result: object | None = None


__all__ = ["Job", "JobStatus"]
