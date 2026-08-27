"""Small synchronous Ollama HTTP client; model weights stay on the PC."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OllamaRuntime:
    base_url: str = "http://127.0.0.1:11434"
    connect_timeout: float = 5.0
    request_timeout: float = 1800.0

    def _request(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST" if data is not None else "GET",
        )
        timeout = self.request_timeout if data is not None else self.connect_timeout
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"Ollama is unavailable: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError("Ollama returned invalid JSON.") from exc

    def health(self) -> bool:
        try:
            self._request("/api/tags")
            return True
        except RuntimeError:
            return False

    def generate(self, model: str, prompt: str, *, temperature: float = 0.1, context: int = 32768) -> str:
        if not model.strip() or not prompt.strip():
            raise ValueError("model and prompt are required")
        result = self._request(
            "/api/generate",
            {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_ctx": context},
            },
        )
        text = str(result.get("response", ""))
        if not text:
            raise RuntimeError("Ollama returned an empty response.")
        return text


__all__ = ["OllamaRuntime"]
