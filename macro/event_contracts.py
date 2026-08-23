from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class EventImpact(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass(frozen=True, slots=True)
class MarketEvent:
    event_id: str
    timestamp: int
    title: str
    impact: EventImpact
    assets: tuple[str, ...] = ()
    sentiment: float | None = None

class EventRiskGate:
    def blocked(self, events: tuple[MarketEvent, ...], now: int, horizon_seconds: int) -> bool:
        return any(e.timestamp >= now and e.timestamp <= now + horizon_seconds and e.impact in {EventImpact.HIGH, EventImpact.CRITICAL} for e in events)
