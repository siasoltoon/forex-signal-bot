from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class JobPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class Job:
    job_id: str
    job_type: str
    priority: JobPriority = JobPriority.NORMAL
    status: JobStatus = JobStatus.QUEUED
    payload: Mapping[str, Any] = field(default_factory=dict)
    retry_count: int = 0

    @classmethod
    def create(cls, job_type: str, payload: Mapping[str, Any] | None = None, priority: JobPriority = JobPriority.NORMAL) -> "Job":
        return cls(uuid4().hex, job_type, priority, payload=payload or {})


@dataclass(frozen=True, slots=True)
class WorkerCapabilities:
    cpu_cores: int
    memory_mb: int
    gpu_available: bool = False
    supported_job_types: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class WorkerHeartbeat:
    worker_id: str
    online: bool
    busy: bool
    cpu_percent: float
    memory_percent: float
    current_job_id: str | None = None


@dataclass(frozen=True, slots=True)
class AlertEvent:
    event_type: str
    severity: str
    entity_id: str
    message_key: str
    metadata: Mapping[str, Any] = field(default_factory=dict)
