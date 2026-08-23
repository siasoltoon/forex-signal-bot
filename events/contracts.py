from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DomainEvent:
    event_id: str
    event_type: str
    aggregate_id: str
    occurred_at: str
    payload: dict[str, object]
    version: int = 1


@dataclass(frozen=True, slots=True)
class EventEnvelope:
    event: DomainEvent
    correlation_id: str
    causation_id: str | None = None


__all__ = ["DomainEvent", "EventEnvelope"]
