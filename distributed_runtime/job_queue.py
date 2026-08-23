from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock

from .runtime_contracts import Job, JobPriority, JobStatus


class InMemoryJobQueue:
    """Thread-safe queue boundary; persistent queues can implement the same contract."""

    _ORDER = (JobPriority.CRITICAL, JobPriority.HIGH, JobPriority.NORMAL, JobPriority.LOW)

    def __init__(self) -> None:
        self._queues: dict[JobPriority, deque[Job]] = defaultdict(deque)
        self._lock = Lock()

    def enqueue(self, job: Job) -> None:
        with self._lock:
            self._queues[job.priority].append(job)

    def depth(self) -> int:
        with self._lock:
            return sum(len(queue) for queue in self._queues.values())

    def dequeue(self, supported_types: frozenset[str] | None = None) -> Job | None:
        with self._lock:
            for priority in self._ORDER:
                queue = self._queues[priority]
                for _ in range(len(queue)):
                    job = queue.popleft()
                    if not supported_types or job.job_type in supported_types:
                        return job
                    queue.append(job)
        return None

    @staticmethod
    def mark_running(job: Job) -> Job:
        return Job(job.job_id, job.job_type, job.priority, JobStatus.RUNNING, job.payload, job.retry_count)

    @staticmethod
    def mark_failed(job: Job) -> Job:
        return Job(job.job_id, job.job_type, job.priority, JobStatus.FAILED, job.payload, job.retry_count + 1)
