from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
from collections.abc import Callable
from urllib.parse import urlsplit


class _HealthHandler(BaseHTTPRequestHandler):
    server_version = "ForexSignalHealth/1.0"

    def do_GET(self) -> None:  # noqa: N802
        request_path = urlsplit(self.path).path
        if request_path == "/health":
            payload = self.server.health_provider()  # type: ignore[attr-defined]
            self._write_json(payload, _http_status_for_health(payload))
            return
        if request_path == "/worker/health":
            gateway = getattr(self.server, "worker_gateway", None)
            if gateway is None:
                self.send_error(404)
                return
            if not self._authorized(gateway):
                self._write_json({"error": "unauthorized"}, 401)
                return
            self._write_json(gateway.health(), 200)
            return
        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        request_path = urlsplit(self.path).path
        gateway = getattr(self.server, "worker_gateway", None)
        if gateway is None or request_path not in {"/worker/claim", "/worker/renew", "/worker/result"}:
            self.send_error(404)
            return
        if not self._authorized(gateway):
            self._write_json({"error": "unauthorized"}, 401)
            return

        try:
            payload = self._read_json()
            if request_path == "/worker/claim":
                result = gateway.claim()
                self._write_json(result or {"status": "EMPTY"}, 200)
                return
            if request_path == "/worker/renew":
                result = gateway.renew(payload)
                self._write_json(result, 200)
                return
            result = gateway.result(payload)
            self._write_json(result, 200)
        except ValueError as exc:
            self._write_json({"error": str(exc)}, 400)
        except KeyError as exc:
            self._write_json({"error": f"unknown job: {exc.args[0]}"}, 404)
        except Exception:
            self._write_json({"error": "worker gateway internal error"}, 500)

    def _authorized(self, gateway: object) -> bool:
        authenticate = getattr(gateway, "authenticate", None)
        if not callable(authenticate):
            return False
        return bool(authenticate(self.headers.get("Authorization")))

    def _read_json(self) -> dict:
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            raise ValueError("Content-Type must be application/json")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("Invalid Content-Length") from exc
        if length < 0 or length > 5 * 1024 * 1024:
            raise ValueError("Request body is too large")
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Invalid JSON body") from exc
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object")
        return payload

    def _write_json(self, payload: object, status: int) -> None:
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def _http_status_for_health(payload: object) -> int:
    if not isinstance(payload, dict):
        return 503
    application = payload.get("application")
    if isinstance(application, dict):
        status = application.get("status")
        if status in {"degraded", "error", "unhealthy"}:
            return 503
    top_level_status = payload.get("status")
    if top_level_status in {"degraded", "error", "unhealthy"}:
        return 503
    return 200


class HealthServer:
    """Small HTTP endpoint for health and authenticated PC-worker pull traffic."""

    def __init__(
        self,
        health_provider: Callable[[], dict],
        *,
        host: str = "0.0.0.0",
        port: int = 8080,
    ) -> None:
        if not 0 <= port <= 65535:
            raise ValueError("health server port must be between 0 and 65535")

        self._server = ThreadingHTTPServer((host, port), _HealthHandler)
        self._server.health_provider = health_provider  # type: ignore[attr-defined]
        self._server.worker_gateway = None  # type: ignore[attr-defined]
        self._thread: threading.Thread | None = None

    @property
    def port(self) -> int:
        return int(self._server.server_address[1])

    def set_worker_gateway(self, gateway: object | None) -> None:
        self._server.worker_gateway = gateway  # type: ignore[attr-defined]

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="health-server",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        if self._thread:
            self._server.shutdown()
            self._thread.join(timeout=2)
            self._thread = None
        self._server.server_close()
