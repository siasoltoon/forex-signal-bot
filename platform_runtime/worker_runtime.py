from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping


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


@dataclass(frozen=True)
class WorkerJob:
    job_id: str
    job_type: str
    priority: int
    payload: Mapping[str, Any]
    created_at: datetime
    retries: int = 0


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
