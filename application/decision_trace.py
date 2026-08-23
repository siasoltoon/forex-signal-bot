from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class DecisionTraceEvent:
    stage: str
    event: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    evidence: Mapping[str, Any] = field(default_factory=dict)


class DecisionTrace:
    def __init__(self) -> None:
        self._events: list[DecisionTraceEvent] = []

    def record(self, stage: str, event: str, evidence: Mapping[str, Any] | None = None) -> None:
        self._events.append(DecisionTraceEvent(stage, event, evidence=evidence or {}))

    def events(self) -> tuple[DecisionTraceEvent, ...]:
        return tuple(self._events)

    def export(self) -> tuple[dict[str, Any], ...]:
        return tuple({"stage": e.stage, "event": e.event, "timestamp": e.timestamp.isoformat(), "evidence": dict(e.evidence)} for e in self._events)
