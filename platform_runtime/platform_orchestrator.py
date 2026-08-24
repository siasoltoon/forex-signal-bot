from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

from .live import LiveEvent, LiveMonitor, LiveSignal
from .production import AuditEvent, AuditLog, HealthRegistry, HealthStatus, Severity
from .worker import Job, JobQueue, WorkerRegistry


@dataclass(frozen=True)
class RuntimeHealth:
    healthy: bool
    components: tuple[HealthStatus, ...]


class PlatformOrchestrator:
    """Coordinates queue, worker, live monitoring and production observability.

    Network/API integrations remain injected dependencies. This layer never
    fabricates prices, news, model predictions, or execution fills.
    """

    def __init__(self, jobs: JobQueue | None = None, workers: WorkerRegistry | None = None, audit: AuditLog | None = None) -> None:
        self.jobs = jobs or JobQueue()
        self.workers = workers or WorkerRegistry()
        self.health = HealthRegistry()
        self.audit = audit or AuditLog()
        self.live = LiveMonitor(on_event=self._record_live_event)

    def submit_heavy_job(self, job_type: str, payload: dict, priority: int = 0) -> str:
        job_id = self.jobs.submit(Job(type=job_type, payload=payload, priority=priority))
        self.audit.record(AuditEvent("job_submitted", "platform_orchestrator", Severity.INFO, job_id=job_id))
        return job_id

    def claim_job(self, worker_id: str) -> Job | None:
        job = self.jobs.claim(worker_id)
        self.health.update(HealthStatus("worker_queue", True, {"worker_id": worker_id, "claimed": bool(job)}))
        return job

    def register_live_signal(self, signal: LiveSignal) -> None:
        self.live.register(signal)
        self.audit.record(AuditEvent("live_signal_registered", "live_monitor", Severity.INFO, metadata={"signal_id": signal.signal_id}))

    def update_live_signal(self, signal_id: str, price: float, confidence: float | None = None, invalidated: bool = False) -> list[LiveEvent]:
        return self.live.update(signal_id, price, confidence, invalidated)

    def health_snapshot(self) -> RuntimeHealth:
        components = self.health.all()
        return RuntimeHealth(self.health.healthy(), components)

    def _record_live_event(self, event: LiveEvent) -> None:
        severity = Severity.CRITICAL if event.severity == "critical" else Severity.WARNING
        self.audit.record(AuditEvent("live_event", "live_monitor", severity, metadata={"signal_id": event.signal_id, "kind": event.kind, "message": event.message}))


__all__ = ["PlatformOrchestrator", "RuntimeHealth"]
