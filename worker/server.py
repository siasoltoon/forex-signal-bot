from __future__ import annotations

import hashlib
import hmac
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .contracts import JobRequest
from .runtime import WorkerRuntime


class WorkerHTTPServer:
    def __init__(self, runtime: WorkerRuntime, host: str | None = None, port: int | None = None, token: str | None = None):
        self.runtime = runtime
        self.host = host or os.getenv("PC_WORKER_HOST", "127.0.0.1")
        self.port = port or int(os.getenv("PC_WORKER_PORT", "8765"))
        self.token = token or os.getenv("PC_WORKER_TOKEN", "")
        if not self.token:
            raise ValueError("PC_WORKER_TOKEN must be configured")
        runtime_ref = runtime
        token_ref = self.token

        class Handler(BaseHTTPRequestHandler):
            def _authorized(self) -> bool:
                supplied = self.headers.get("Authorization", "")
                expected = f"Bearer {token_ref}"
                return hmac.compare_digest(supplied, expected)

            def _json(self, status: int, payload: dict[str, Any]) -> None:
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self) -> None:  # noqa: N802
                if self.path != "/health":
                    self._json(404, {"error": "not_found"}); return
                self._json(200, runtime_ref.health())

            def do_POST(self) -> None:  # noqa: N802
                if self.path != "/jobs":
                    self._json(404, {"error": "not_found"}); return
                if not self._authorized():
                    self._json(401, {"error": "unauthorized"}); return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length > 5_000_000:
                        self._json(413, {"error": "payload_too_large"}); return
                    payload = json.loads(self.rfile.read(length))
                    request = JobRequest(job_id=str(payload["job_id"]), job_type=str(payload["job_type"]), payload=dict(payload.get("payload", {})), priority=int(payload.get("priority", 50)), timeout_seconds=min(int(payload.get("timeout_seconds", 3600)), 86_400), allow_cpu_fallback=bool(payload.get("allow_cpu_fallback", True)))
                    import asyncio
                    result = asyncio.run(runtime_ref.execute(request))
                    self._json(200, {"job_id": result.job_id, "status": result.status, "job_type": result.job_type, "output": result.output, "error": result.error, "worker_id": result.worker_id})
                except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
                    self._json(400, {"error": f"invalid_request: {exc}"})
                except Exception as exc:
                    self._json(500, {"error": f"internal_error: {type(exc).__name__}: {exc}"})

            def log_message(self, format: str, *args: Any) -> None:
                return

        self._server = ThreadingHTTPServer((self.host, self.port), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, name="pc-worker-http", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()


__all__ = ["WorkerHTTPServer"]
