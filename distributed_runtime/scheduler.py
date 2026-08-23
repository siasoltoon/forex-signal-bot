from __future__ import annotations

from .runtime_contracts import Job, WorkerCapabilities


class ResourceAwareScheduler:
    """Selects workers using declared capabilities only; no workload is fabricated."""

    @staticmethod
    def can_run(job: Job, capabilities: WorkerCapabilities) -> bool:
        return not capabilities.supported_job_types or job.job_type in capabilities.supported_job_types

    def select(self, job: Job, workers: tuple[tuple[str, WorkerCapabilities], ...]) -> str | None:
        candidates = [(worker_id, caps) for worker_id, caps in workers if self.can_run(job, caps)]
        if not candidates:
            return None
        candidates.sort(key=lambda item: (not item[1].gpu_available, -item[1].cpu_cores, -item[1].memory_mb))
        return candidates[0][0]
