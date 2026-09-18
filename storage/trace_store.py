from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from storage.repository import InMemoryRepository


@dataclass(frozen=True, slots=True)
class TraceRecord:
    trace_id: str
    analysis_id: str
    created_at: datetime
    stages: tuple[tuple[str, Any], ...] = ()


class DecisionTraceStore:
    def __init__(self) -> None:
        self._repository = InMemoryRepository(lambda item: item.trace_id)

    def append(self, trace: TraceRecord) -> None:
        self._repository.save(trace)

    def get(self, trace_id: str) -> TraceRecord | None:
        return self._repository.get(trace_id)

    def list_for_analysis(self, analysis_id: str) -> tuple[TraceRecord, ...]:
        return tuple(item for item in self._repository.list() if item.analysis_id == analysis_id)
