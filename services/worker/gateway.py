from __future__ import annotations

import hmac
from typing import Any

from worker.contracts import JobResult
from worker.dispatcher import WorkerDispatcher


class WorkerGateway:
    """Authenticated pull gateway for a remote PC Worker.

    The PC Worker makes outbound HTTPS requests to Railway, claims a queued
    job, executes it locally, and posts the fenced result back.
    """

    def __init__(self, dispatcher: WorkerDispatcher, token: str) -> None:
        if not token:
            raise ValueError("PC_WORKER_TOKEN must be configured for pull mode")
        self.dispatcher = dispatcher
        self.token = token

    def authenticate(self, authorization: str | None) -> bool:
        if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
            return False
        presented = authorization[7:].strip()
        return bool(presented) and hmac.compare_digest(presented, self.token)

    def claim(self) -> dict[str, Any] | None:
        record = self.dispatcher.claim_next()
        if record is None:
            return None
        return {
            "job_id": record.job_id,
            "job_type": record.job_type,
            "payload": record.payload,
            "priority": record.priority,
            "timeout_seconds": record.timeout_seconds,
            "allow_cpu_fallback": record.allow_cpu_fallback,
            "claim_token": record.claim_token,
        }

    def result(self, payload: dict[str, Any]) -> dict[str, Any]:
        required = ("job_id", "job_type", "status", "claim_token")
        if any(not isinstance(payload.get(key), str) or not payload[key].strip() for key in required):
            raise ValueError("job_id, job_type, status and claim_token are required")

        result = JobResult(
            job_id=payload["job_id"],
            status=payload["status"],
            job_type=payload["job_type"],
            output=payload.get("output") if isinstance(payload.get("output"), dict) else {},
            error=payload.get("error") if isinstance(payload.get("error"), str) else None,
            worker_id=payload.get("worker_id") if isinstance(payload.get("worker_id"), str) else None,
        )
        return self.dispatcher.apply_remote_result(result, payload["claim_token"])

    def health(self) -> dict[str, Any]:
        return {
            "status": "READY",
            "mode": "pull",
            "queue": self.dispatcher.health().get("queue", {}),
        }


__all__ = ["WorkerGateway"]
