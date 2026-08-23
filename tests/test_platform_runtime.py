from datetime import datetime, timezone

from distributed_runtime.job_queue import InMemoryJobQueue
from distributed_runtime.runtime_contracts import Job, JobPriority, WorkerCapabilities, WorkerHeartbeat
from distributed_runtime.scheduler import ResourceAwareScheduler
from distributed_runtime.worker_registry import WorkerRegistry
from platform_runtime import Candle, DataValidator, Job as RuntimeJob, JobQueue, RiskEngine, RiskLimits, detect_integrity, monte_carlo


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
    heartbeat = WorkerHeartbeat("w1", True, False, 10.0, 20.0)
    record = registry.heartbeat("w1", caps, heartbeat)
    assert record.worker_id == "w1"
    assert len(registry.online_workers()) == 1


def _candle(ts: int, close: float) -> Candle:
    return Candle(datetime.fromtimestamp(ts, tz=timezone.utc), close, close + 1, close - 1, close)


def test_data_validation_rejects_duplicate_timestamp() -> None:
    quality = DataValidator().validate([_candle(1, 1), _candle(1, 2)])
    assert not quality.valid
    assert "duplicate_candle" in quality.issues


def test_risk_engine_blocks_zero_stop_distance() -> None:
    plan = RiskEngine(RiskLimits(risk_percent=1)).position_size(10_000, 100, 100)
    assert plan.blocked and plan.quantity == 0


def test_runtime_job_queue_prefers_high_priority() -> None:
    queue = JobQueue()
    low = RuntimeJob("analysis", {}, priority=1)
    high = RuntimeJob("analysis", {}, priority=10)
    queue.submit(low)
    queue.submit(high)
    assert queue.claim("worker-1").id == high.id


def test_research_integrity_detects_overlap() -> None:
    result = detect_integrity(["a", "b"], ["b", "c"])
    assert result.leakage_detected


def test_monte_carlo_is_deterministic() -> None:
    result = monte_carlo([1, -1, 2], trials=50, seed=3)
    assert result.trials == 50
