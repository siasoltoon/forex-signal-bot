from __future__ import annotations

from storage.contracts import JobRecord
from storage.repository import Repository


class JobStore:
    def __init__(self, repository: Repository[JobRecord]) -> None:
        self._repository = repository

    def put(self, job: JobRecord) -> None:
        self._repository.save(job)

    def get(self, job_id: str) -> JobRecord | None:
        return self._repository.get(job_id)

    def by_status(self, status: str) -> tuple[JobRecord, ...]:
        return tuple(job for job in self._repository.list() if job.status == status)

    def by_worker(self, worker_id: str) -> tuple[JobRecord, ...]:
        return tuple(job for job in self._repository.list() if job.worker_id == worker_id)
