from __future__ import annotations

import asyncio
import json
import logging
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .contracts import JobRequest, JobResult
from .runtime import WorkerRuntime

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkerPullSettings:
    base_url: str
    token: str
    poll_interval_seconds: float = 3.0
    request_timeout_seconds: int = 30

    @classmethod
    def from_env(cls) -> "WorkerPullSettings | None":
        base_url = os.getenv("WORKER_QUEUE_API_URL", "").strip().rstrip("/")
        token = os.getenv("PC_WORKER_TOKEN", "").strip()
        if not base_url:
            return None
        if not token:
            raise ValueError("PC_WORKER_TOKEN must be configured when WORKER_QUEUE_API_URL is set")
        interval = float(os.getenv("WORKER_QUEUE_POLL_INTERVAL", "3"))
        timeout = int(os.getenv("WORKER_QUEUE_REQUEST_TIMEOUT", "30"))
        if interval <= 0 or timeout <= 0:
            raise ValueError("Worker pull intervals and timeouts must be positive")
        return cls(base_url, token, interval, timeout)


class WorkerPullClient:
    """Pulls durable jobs from Railway over outbound HTTPS."""

    def __init__(self, settings: WorkerPullSettings) -> None:
        self.settings = settings

    def _request(self, path: str, method: str = "POST", payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(
            f"{self.settings.base_url}{path}",
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self.settings.token}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=self.settings.request_timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Worker gateway response must be a JSON object")
        return data

    def claim(self) -> dict[str, Any] | None:
        data = self._request("/worker/claim")
        if data.get("status") == "EMPTY":
            return None
        return data

    def renew(self, job_id: str, claim_token: str) -> dict[str, Any]:
        return self._request("/worker/renew", payload={"job_id": job_id, "claim_token": claim_token})

    def submit_result(self, result: JobResult, claim_token: str) -> dict[str, Any]:
        return self._request(
            "/worker/result",
            payload={
                "job_id": result.job_id,
                "job_type": result.job_type,
                "status": result.status,
                "output": result.output,
                "error": result.error,
                "worker_id": result.worker_id,
                "claim_token": claim_token,
            },
        )

    async def _renew_loop(self, job_id: str, claim_token: str, timeout_seconds: int, stop_event: asyncio.Event) -> None:
        interval = min(30.0, max(1.0, timeout_seconds / 3.0))
        while not stop_event.is_set():
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval)
                return
            except asyncio.TimeoutError:
                pass
            try:
                response = await asyncio.to_thread(self.renew, job_id, claim_token)
                if response.get("status") != "RUNNING":
                    logger.warning("Worker claim lease is no longer RUNNING: %s", job_id)
                    return
            except Exception as exc:
                logger.warning("Failed to renew worker claim %s: %s", job_id, exc)

    async def run(self, runtime: WorkerRuntime, stop_event: asyncio.Event) -> None:
        while not stop_event.is_set():
            try:
                claim = await asyncio.to_thread(self.claim)
                if claim is not None:
                    request = JobRequest(
                        job_id=str(claim["job_id"]),
                        job_type=str(claim["job_type"]),
                        payload=claim.get("payload") if isinstance(claim.get("payload"), dict) else {},
                        priority=int(claim.get("priority", 50)),
                        timeout_seconds=int(claim.get("timeout_seconds", 3600)),
                        allow_cpu_fallback=bool(claim.get("allow_cpu_fallback", True)),
                    )
                    claim_token = str(claim["claim_token"])
                    lease_stop = asyncio.Event()
                    lease_task = asyncio.create_task(
                        self._renew_loop(request.job_id, claim_token, request.timeout_seconds, lease_stop)
                    )
                    try:
                        result = await runtime.execute(request)
                    finally:
                        lease_stop.set()
                        lease_task.cancel()
                        await asyncio.gather(lease_task, return_exceptions=True)
                    await asyncio.to_thread(self.submit_result, result, claim_token)
                    continue
            except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
                logger.warning("PC Worker pull transport unavailable: %s", exc)
            except Exception:
                logger.exception("Unexpected PC Worker pull-loop failure")
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=self.settings.poll_interval_seconds)
            except asyncio.TimeoutError:
                pass


__all__ = ["WorkerPullClient", "WorkerPullSettings"]
