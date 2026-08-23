from __future__ import annotations

from threading import Lock

from .contracts import AnalysisRecord, UserSettings


class InMemoryAnalysisRepository:
    def __init__(self) -> None:
        self._items: dict[str, AnalysisRecord] = {}
        self._lock = Lock()

    def save(self, record: AnalysisRecord) -> None:
        with self._lock:
            self._items[record.analysis_id] = record

    def get(self, analysis_id: str) -> AnalysisRecord | None:
        with self._lock:
            return self._items.get(analysis_id)

    def list_for_user(self, user_id: str, limit: int = 50) -> tuple[AnalysisRecord, ...]:
        with self._lock:
            items = [x for x in self._items.values() if x.user_id == user_id]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return tuple(items[: max(0, limit)])


class InMemorySettingsRepository:
    def __init__(self) -> None:
        self._items: dict[str, UserSettings] = {}
        self._lock = Lock()

    def get(self, user_id: str) -> UserSettings | None:
        with self._lock:
            return self._items.get(user_id)

    def save(self, settings: UserSettings) -> None:
        with self._lock:
            self._items[settings.user_id] = settings
