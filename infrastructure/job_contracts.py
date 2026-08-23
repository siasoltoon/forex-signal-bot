from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"

@dataclass(frozen=True, slots=True)
class Job:
    id: str
    type: str
    priority: int = 0
    status: JobStatus = JobStatus.QUEUED
    retry_count: int = 0

@dataclass(frozen=True, slots=True)
class WorkerHeartbeat:
    worker_id: str
    online: bool
    cpu: float
    ram: float
    gpu: float | None = None
    current_job: str | None = None
