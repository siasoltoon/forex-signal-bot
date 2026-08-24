from __future__ import annotations

from datetime import datetime, timezone
from workers.contracts import WorkerHeartbeat, WorkerState


class WorkerRegistry:
    def __init__(self, *, heartbeat_timeout_seconds: int = 60) -> None:
        if heartbeat_timeout_seconds <= 0:
            raise ValueError("heartbeat timeout must be positive")
        self.heartbeat_timeout_seconds = heartbeat_timeout_seconds
        self._workers: dict[str, WorkerHeartbeat] = {}

    def heartbeat(self, heartbeat: WorkerHeartbeat) -> None:
        self._workers[heartbeat.worker_id] = heartbeat

    def get(self, worker_id: str) -> WorkerHeartbeat | None:
        self._refresh(worker_id)
        return self._workers.get(worker_id)

    def all(self) -> tuple[WorkerHeartbeat, ...]:
        for worker_id in tuple(self._workers):
            self._refresh(worker_id)
        return tuple(self._workers.values())

    def _refresh(self, worker_id: str) -> None:
        heartbeat = self._workers.get(worker_id)
        if heartbeat is None:
            return
        age = (datetime.now(timezone.utc) - heartbeat.at).total_seconds()
        if age > self.heartbeat_timeout_seconds:
            self._workers[worker_id] = WorkerHeartbeat(
                worker_id=heartbeat.worker_id,
                state=WorkerState.OFFLINE,
                resources=heartbeat.resources,
                current_job_id=None,
                at=heartbeat.at,
            )
