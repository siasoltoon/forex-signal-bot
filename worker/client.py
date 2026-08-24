from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from .contracts import JobRequest, JobResult


class PCWorkerClient:
    """Railway-side client for submitting heavy jobs to the optional PC Worker."""

    def __init__(self, base_url: str, token: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def health(self) -> dict[str, Any]:
        request = urllib.request.Request(f"{self.base_url}/health", method="GET")
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def submit(self, job: JobRequest) -> JobResult:
        body = json.dumps({
            "job_id": job.job_id,
            "job_type": job.job_type,
            "payload": job.payload,
            "priority": job.priority,
            "timeout_seconds": job.timeout_seconds,
            "allow_cpu_fallback": job.allow_cpu_fallback,
        }).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/jobs",
            data=body,
            method="POST",
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=max(self.timeout, job.timeout_seconds)) as response:
                data = json.loads(response.read().decode("utf-8"))
            return JobResult(data["job_id"], data["status"], data["job_type"], data.get("output", {}), data.get("error"), data.get("worker_id"))
        except (urllib.error.URLError, TimeoutError) as exc:
            return JobResult(job.job_id, "WORKER_OFFLINE", job.job_type, error=str(exc))
