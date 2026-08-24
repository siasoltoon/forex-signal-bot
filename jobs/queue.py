from __future__ import annotations

from collections import deque
from threading import Lock

from jobs.contracts import Job, JobPriority


_PRIORITY = {JobPriority.CRITICAL: 0, JobPriority.HIGH: 1, JobPriority.NORMAL: 2, JobPriority.LOW: 3}


class JobQueue:
    def __init__(self, *, max_size: int = 10000) -> None:
        if max_size <= 0:
            raise ValueError("max_size must be positive")
        self.max_size = max_size
        self._items: list[tuple[int, int, Job]] = []
        self._sequence = 0
        self._lock = Lock()

    def enqueue(self, job: Job) -> None:
        with self._lock:
            if len(self._items) >= self.max_size:
                raise OverflowError("job queue is full")
            self._items.append((_PRIORITY[job.priority], self._sequence, job))
            self._sequence += 1

    def dequeue(self) -> Job | None:
        with self._lock:
            if not self._items:
                return None
            index = min(range(len(self._items)), key=lambda i: (self._items[i][0], self._items[i][1]))
            return self._items.pop(index)[2]

    def size(self) -> int:
        with self._lock:
            return len(self._items)
