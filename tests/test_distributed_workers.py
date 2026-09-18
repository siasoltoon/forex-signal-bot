from datetime import datetime, timedelta, timezone

import pytest

from jobs.contracts import Job, JobPriority
from jobs.queue import JobQueue
from workers.contracts import ResourceSnapshot, WorkerHeartbeat, WorkerState
from workers.executor import WorkerExecutor
from workers.registry import WorkerRegistry
from workers.scheduler import ResourceAwareScheduler
from workers.security import JobAuthenticator


def test_priority_queue_orders_critical_first() -> None:
    queue = JobQueue()
    queue.enqueue(Job("light", priority=JobPriority.LOW))
    critical = Job("heavy", priority=JobPriority.CRITICAL)
    queue.enqueue(critical)
    assert queue.dequeue() == critical


def test_worker_registry_marks_stale_worker_offline() -> None:
    registry = WorkerRegistry(heartbeat_timeout_seconds=10)
    heartbeat = WorkerHeartbeat("pc-1", WorkerState.IDLE, ResourceSnapshot(), at=datetime.now(timezone.utc) - timedelta(seconds=20))
    registry.heartbeat(heartbeat)
    assert registry.get("pc-1").state == WorkerState.OFFLINE


def test_scheduler_rejects_busy_or_overloaded_worker() -> None:
    scheduler = ResourceAwareScheduler()
    job = Job("heavy")
    busy = WorkerHeartbeat("pc-1", WorkerState.BUSY, ResourceSnapshot())
    overloaded = WorkerHeartbeat("pc-2", WorkerState.IDLE, ResourceSnapshot(cpu_percent=95))
    assert scheduler.can_accept(job, busy) is False
    assert scheduler.can_accept(job, overloaded) is False


def test_executor_returns_failure_for_unknown_job() -> None:
    result = WorkerExecutor("pc-1", {}).execute(Job("unknown"))
    assert result.success is False
    assert result.error == "unsupported_job_type"


def test_job_authentication_is_signed_and_verifiable() -> None:
    auth = JobAuthenticator("secret")
    signature = auth.sign("job-payload")
    assert auth.verify("job-payload", signature)
    assert not auth.verify("tampered", signature)
