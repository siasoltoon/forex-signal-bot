from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


class WorkerState(StrEnum):
    OFFLINE = "OFFLINE"
    STARTING = "STARTING"
    IDLE = "IDLE"
    BUSY = "BUSY"
    DRAINING = "DRAINING"
    UNHEALTHY = "UNHEALTHY"


@dataclass(frozen=True, slots=True)
class ResourceSnapshot:
    cpu_percent: float = 0.0
    ram_percent: float = 0.0
    gpu_percent: float | None = None
    disk_percent: float = 0.0
    network_mbps: float = 0.0

    def __post_init__(self) -> None:
        for value in (self.cpu_percent, self.ram_percent, self.disk_percent):
            if not 0 <= value <= 100:
                raise ValueError("resource percentages must be between 0 and 100")
        if self.gpu_percent is not None and not 0 <= self.gpu_percent <= 100:
            raise ValueError("gpu percentage must be between 0 and 100")


@dataclass(frozen=True, slots=True)
class WorkerHeartbeat:
    worker_id: str
    state: WorkerState
    resources: ResourceSnapshot
    current_job_id: str | None = None
    at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True)
class JobResult:
    job_id: str
    success: bool
    worker_id: str
    output: tuple[tuple[str, str], ...] = ()
    error: str | None = None
