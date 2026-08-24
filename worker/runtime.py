from __future__ import annotations

import asyncio
import logging
import os
import platform
import socket
import uuid
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from .contracts import JobRequest, JobResult, WorkerCapabilities

logger = logging.getLogger(__name__)
Handler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]] | dict[str, Any]]


@dataclass
class WorkerRuntime:
    worker_id: str
    capabilities: WorkerCapabilities
    handlers: dict[str, Handler]

    @classmethod
    def create(cls) -> "WorkerRuntime":
        worker_id = os.getenv("PC_WORKER_ID") or f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
        gpu = os.getenv("PC_WORKER_GPU", "1").lower() not in {"0", "false", "no"}
        capabilities = WorkerCapabilities(gpu=gpu, max_ram_gb=int(os.getenv("PC_WORKER_RAM_GB", "16")))
        return cls(worker_id=worker_id, capabilities=capabilities, handlers={})

    def register(self, job_type: str, handler: Handler) -> None:
        if job_type not in self.capabilities.supported_jobs:
            raise ValueError(f"Unsupported worker job type: {job_type}")
        self.handlers[job_type] = handler

    def health(self) -> dict[str, Any]:
        return {"worker_id": self.worker_id, "status": "READY", "hostname": socket.gethostname(), "platform": platform.platform(), "python": platform.python_version(), "cpu": self.capabilities.cpu, "gpu": self.capabilities.gpu, "max_ram_gb": self.capabilities.max_ram_gb, "registered_jobs": sorted(self.handlers), "limited_jobs": sorted(self.capabilities.limited_jobs)}

    async def execute(self, request: JobRequest) -> JobResult:
        if request.job_type not in self.capabilities.supported_jobs:
            return JobResult(request.job_id, "UNSUPPORTED", request.job_type, error="Unsupported job type", worker_id=self.worker_id)
        handler = self.handlers.get(request.job_type)
        if handler is None:
            return JobResult(request.job_id, "UNSUPPORTED", request.job_type, error="No handler registered", worker_id=self.worker_id)
        try:
            result = handler(request.payload)
            if asyncio.iscoroutine(result):
                result = await asyncio.wait_for(result, timeout=request.timeout_seconds)
            return JobResult(request.job_id, "COMPLETED", request.job_type, output=dict(result or {}), worker_id=self.worker_id)
        except asyncio.TimeoutError:
            return JobResult(request.job_id, "TIMEOUT", request.job_type, error="Worker job timeout", worker_id=self.worker_id)
        except Exception as exc:
            logger.exception("Worker job failed: %s", request.job_id)
            return JobResult(request.job_id, "FAILED", request.job_type, error=f"{type(exc).__name__}: {exc}", worker_id=self.worker_id)


__all__ = ["WorkerRuntime"]
