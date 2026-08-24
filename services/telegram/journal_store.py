from __future__ import annotations

import json
from pathlib import Path
from threading import Lock


class JournalStore:
    """Small dependency-free persistent journal store suitable for Railway volumes."""

    def __init__(self, path: str = "data/journal.json"):
        self.path = Path(path)
        self._lock = Lock()

    def _read(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.path)

    def add(self, user_id: int, entry: dict) -> None:
        with self._lock:
            data = self._read()
            data.setdefault(str(user_id), []).append(entry)
            self._write(data)

    def list(self, user_id: int, limit: int = 20) -> list[dict]:
        with self._lock:
            data = self._read()
            return list(reversed(data.get(str(user_id), [])))[:limit]

    def replace(self, user_id: int, entries: list[dict]) -> None:
        with self._lock:
            data = self._read()
            data[str(user_id)] = entries
            self._write(data)
