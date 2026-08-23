from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock

from .runtime_contracts import WorkerCapabilities, WorkerHeartbeat


@dataclass(frozen=True, slots=True)
class RegisteredWorker:
    worker_id: str
    capabilities: WorkerCapabilities
    heartbeat: WorkerHeartbeat
    last_seen: datetime


class WorkerRegistry:
    def __init__(self) -> None:
        self._workers: dict[str, RegisteredWorker] = {}
        self._lock = Lock()

    def heartbeat(self, worker_id: str, capabilities: WorkerCapabilities, heartbeat: WorkerHeartbeat) -> RegisteredWorker:
        record = RegisteredWorker(worker_id, capabilities, heartbeat, datetime.now(timezone.utc))
        with self._lock:
            self._workers[worker_id] = record
        return record

    def get(self, worker_id: str) -> RegisteredWorker | None:
        with self._lock:
            return self._workers.get(worker_id)

    def online_workers(self) -> tuple[RegisteredWorker, ...]:
        with self._lock:
            return tuple(worker for worker in self._workers.values() if worker.heartbeat.online)
