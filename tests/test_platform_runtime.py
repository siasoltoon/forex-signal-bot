from platform.job_queue import InMemoryJobQueue
from platform.runtime_contracts import Job, JobPriority, WorkerCapabilities
from platform.scheduler import ResourceAwareScheduler
from platform.worker_registry import WorkerRegistry


def test_priority_queue_prefers_critical_jobs() -> None:
    queue = InMemoryJobQueue()
    queue.enqueue(Job.create("analysis", priority=JobPriority.NORMAL))
    critical = Job.create("analysis", priority=JobPriority.CRITICAL)
    queue.enqueue(critical)
    assert queue.dequeue().job_id == critical.job_id


def test_scheduler_requires_supported_job_type() -> None:
    job = Job.create("heavy_analysis")
    scheduler = ResourceAwareScheduler()
    assert scheduler.select(job, (("worker-1", WorkerCapabilities(4, 8192, False, frozenset({"other"}))),)) is None


def test_worker_registry_records_heartbeat() -> None:
    registry = WorkerRegistry()
    caps = WorkerCapabilities(8, 16384, True, frozenset({"heavy_analysis"}))
    heartbeat = __import__("platform.runtime_contracts", fromlist=["WorkerHeartbeat"]).WorkerHeartbeat("w1", True, False, 10.0, 20.0)
    record = registry.heartbeat("w1", caps, heartbeat)
    assert record.worker_id == "w1"
    assert len(registry.online_workers()) == 1
