from __future__ import annotations

from dataclasses import dataclass

from jobs.contracts import Job
from workers.contracts import ResourceSnapshot, WorkerHeartbeat, WorkerState


@dataclass(frozen=True, slots=True)
class ResourcePolicy:
    max_cpu: float = 85.0
    max_ram: float = 90.0
    max_disk: float = 95.0
    require_gpu_below: bool = False


class ResourceAwareScheduler:
    def __init__(self, policy: ResourcePolicy | None = None) -> None:
        self.policy = policy or ResourcePolicy()

    def can_accept(self, job: Job, worker: WorkerHeartbeat) -> bool:
        if worker.state not in {WorkerState.IDLE, WorkerState.STARTING}:
            return False
        r = worker.resources
        if r.cpu_percent >= self.policy.max_cpu or r.ram_percent >= self.policy.max_ram or r.disk_percent >= self.policy.max_disk:
            return False
        if self.policy.require_gpu_below and (r.gpu_percent is None or r.gpu_percent >= self.policy.max_cpu):
            return False
        return True
