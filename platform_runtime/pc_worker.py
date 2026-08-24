from __future__ import annotations

import asyncio
import os
import socket
from typing import Awaitable, Callable, Mapping

import httpx

from .persistence_security import SecretManager
from .worker_runtime import WorkerJob, WorkerRegistry, WorkerState, WorkerInfo


Handler = Callable[[Mapping], Awaitable[Mapping]]


class PCWorker:
    """Pull-based worker: the PC never talks to Telegram directly."""

    def __init__(self, queue_url: str, shared_secret: bytes, worker_id: str | None = None) -> None:
        self.queue_url = queue_url.rstrip("/")
        self.shared_secret = shared_secret
        self.worker_id = worker_id or f"{socket.gethostname()}:{os.getpid()}"
        self.handlers: dict[str, Handler] = {}
        self.registry = WorkerRegistry()
        self.running = True

    def register(self, job_type: str, handler: Handler) -> None:
        self.handlers[job_type] = handler

    def _headers(self, body: bytes) -> dict[str, str]:
        return {"X-Worker-Id": self.worker_id, "X-Signature": SecretManager.sign_payload(body, self.shared_secret), "Content-Type": "application/json"}

    async def run_once(self) -> bool:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{self.queue_url}/worker/jobs/claim", headers=self._headers(b""))
            if response.status_code == 204:
                return False
            response.raise_for_status()
            job_data = response.json()
            job = WorkerJob(job_id=job_data["job_id"], job_type=job_data["job_type"], priority=int(job_data["priority"]), payload=job_data["payload"], created_at=__import__("datetime").datetime.fromisoformat(job_data["created_at"]))
            self.registry.heartbeat(WorkerInfo(self.worker_id, WorkerState.BUSY, 0.0, 0.0, None, job.job_id, __import__("datetime").datetime.now(__import__("datetime").timezone.utc)))
            try:
                handler = self.handlers[job.job_type]
                result = await handler(job.payload)
                body = __import__("json").dumps({"job_id": job.job_id, "result": result}).encode()
                response = await client.post(f"{self.queue_url}/worker/jobs/result", content=body, headers=self._headers(body))
                response.raise_for_status()
            except Exception as exc:
                body = __import__("json").dumps({"job_id": job.job_id, "error": f"{type(exc).__name__}: {exc}"}).encode()
                await client.post(f"{self.queue_url}/worker/jobs/fail", content=body, headers=self._headers(body))
            finally:
                self.registry.heartbeat(WorkerInfo(self.worker_id, WorkerState.IDLE, 0.0, 0.0, None, None, __import__("datetime").datetime.now(__import__("datetime").timezone.utc)))
            return True

    async def run_forever(self, interval_seconds: float = 2.0) -> None:
        while self.running:
            try:
                await self.run_once()
            except Exception:
                await asyncio.sleep(interval_seconds)
            await asyncio.sleep(interval_seconds)


def from_environment() -> PCWorker:
    secret = os.getenv("WORKER_SHARED_SECRET")
    queue_url = os.getenv("RAILWAY_QUEUE_URL")
    if not secret or not queue_url:
        raise RuntimeError("WORKER_SHARED_SECRET and RAILWAY_QUEUE_URL are required")
    return PCWorker(queue_url, secret.encode())
