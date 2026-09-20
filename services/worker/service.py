from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from typing import Any

from config.settings import Settings
from services.base import BaseService
from worker.client import PCWorkerClient
from worker.contracts import JobRequest, JobResult
from worker.dispatcher import WorkerDispatcher
from worker.gateway import WorkerGateway


class WorkerProcessingService(BaseService):
    """Application boundary for optional heavy PC-worker processing."""

    name = "worker_processing"
    critical = False

    def __init__(
        self,
        dispatcher: WorkerDispatcher,
        configured: bool,
        client: PCWorkerClient | None = None,
        heartbeat_max_age: int = 120,
        pull_mode: bool = False,
        gateway: WorkerGateway | None = None,
    ) -> None:
        if dispatcher is None:
            raise TypeError("dispatcher cannot be None")
        if heartbeat_max_age < 1:
            raise ValueError("heartbeat_max_age must be at least 1 second")
        self.dispatcher = dispatcher
        self.configured = configured
        self.pull_mode = pull_mode
        self._client = client
        self._gateway = gateway
        self._heartbeat_max_age = heartbeat_max_age
        self._last_heartbeat: dict[str, Any] | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "WorkerProcessingService":
        resolved = settings or Settings.load()
        pull_mode = os.getenv("PC_WORKER_MODE", "").strip().lower() == "pull"
        client: PCWorkerClient | None = None

        if resolved.pc_worker_url:
            client = PCWorkerClient(
                resolved.pc_worker_url,
                resolved.pc_worker_token or "",
                timeout=resolved.pc_worker_timeout,
            )

        async def submit(request: JobRequest) -> JobResult:
            if client is None:
                return JobResult(
                    request.job_id,
                    "WORKER_OFFLINE",
                    request.job_type,
                    error="PC worker transport is not configured",
                )
            return await asyncio.to_thread(client.submit, request)

        dispatcher = WorkerDispatcher.from_settings(
            settings=resolved,
            submit=submit if client is not None else None,
        )

        gateway = None
        if pull_mode:
            gateway = WorkerGateway(dispatcher, resolved.pc_worker_token or "")

        return cls(
            dispatcher=dispatcher,
            configured=client is not None or pull_mode,
            client=client,
            heartbeat_max_age=resolved.pc_worker_heartbeat_max_age,
            pull_mode=pull_mode,
            gateway=gateway,
        )

    @property
    def gateway(self) -> WorkerGateway | None:
        return self._gateway

    async def submit(self, request: JobRequest) -> JobResult:
        if self.pull_mode:
            return self.dispatcher.enqueue_only(request)

        if not self.configured:
            return JobResult(
                request.job_id,
                "WORKER_OFFLINE",
                request.job_type,
                error="PC worker transport is not configured",
            )

        readiness = self._heartbeat_readiness()
        if readiness != "READY":
            return JobResult(
                request.job_id,
                "WORKER_OFFLINE",
                request.job_type,
                error=f"PC worker is not ready: {readiness}",
            )

        return await self.dispatcher.submit(request)

    async def submit_many(self, requests: list[JobRequest]) -> list[JobResult]:
        return await asyncio.gather(*(self.submit(request) for request in requests))

    async def heartbeat(self) -> dict[str, Any]:
        if self.pull_mode:
            result = self._gateway.health() if self._gateway else {"status": "WORKER_OFFLINE"}
        elif self._client is None:
            result = {"status": "WORKER_OFFLINE", "configured": False}
        else:
            result = await asyncio.to_thread(self._client.heartbeat)
        self._last_heartbeat = result
        return result

    async def start(self) -> None:
        if self.pull_mode:
            return
        if not self.configured:
            return
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        await self.heartbeat()

    async def _heartbeat_loop(self) -> None:
        while True:
            try:
                result = await self.heartbeat()
                if str(result.get("status", "")).upper() == "READY":
                    await self.dispatcher.dispatch_pending()
            except asyncio.CancelledError:
                raise
            except Exception:
                pass
            await asyncio.sleep(max(10, min(self._heartbeat_max_age // 2, 60)))

    async def stop(self) -> None:
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            await asyncio.gather(self._heartbeat_task, return_exceptions=True)
            self._heartbeat_task = None
        await self.dispatcher.close_async(10.0)

    def _heartbeat_readiness(self) -> str:
        if self._last_heartbeat is None:
            return "UNKNOWN"

        status = str(self._last_heartbeat.get("status", "UNKNOWN")).strip().upper()
        if status != "READY":
            return status or "UNKNOWN"

        worker_id = self._last_heartbeat.get("worker_id")
        if not isinstance(worker_id, str) or not worker_id.strip():
            return "STALE"

        timestamp = self._last_heartbeat.get("timestamp")
        if not isinstance(timestamp, str) or not timestamp.strip():
            return "STALE"

        try:
            heartbeat_time = datetime.fromisoformat(timestamp)
            if heartbeat_time.tzinfo is None:
                return "STALE"
            heartbeat_time = heartbeat_time.astimezone(timezone.utc)
        except (TypeError, ValueError):
            return "STALE"

        age = (datetime.now(timezone.utc) - heartbeat_time).total_seconds()
        if age < 0:
            return "STALE"
        return "READY" if age <= self._heartbeat_max_age else "STALE"

    def health(self) -> dict[str, Any]:
        if self.pull_mode:
            readiness = "READY" if self._gateway is not None else "UNCONFIGURED"
        else:
            readiness = "UNCONFIGURED" if not self.configured else self._heartbeat_readiness()

        health: dict[str, Any] = {
            "service": self.name,
            "status": "ok" if readiness == "READY" else "degraded",
            "critical": self.critical,
            "configured": self.configured,
            "mode": "pull" if self.pull_mode else "push",
            "readiness": readiness,
            "dispatcher": self.dispatcher.health(),
        }
        if self._last_heartbeat is not None:
            for key in ("worker_id", "timestamp"):
                if key in self._last_heartbeat:
                    health[key] = self._last_heartbeat[key]
        return health


__all__ = ["WorkerProcessingService"]
