from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class WorkerStatus(str, Enum):
    OFFLINE = "OFFLINE"
    IDLE = "IDLE"
    BUSY = "BUSY"
    DEGRADED = "DEGRADED"


@dataclass(frozen=True, slots=True)
class WorkerResources:
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    gpu_percent: float | None = None
    disk_percent: float = 0.0


@dataclass(frozen=True, slots=True)
class WorkerInfo:
    worker_id: str
    status: WorkerStatus
    resources: WorkerResources = WorkerResources()
    current_job_id: str | None = None
    last_heartbeat: float | None = None


__all__ = ["WorkerInfo", "WorkerResources", "WorkerStatus"]
