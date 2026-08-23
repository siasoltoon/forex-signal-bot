from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class MonitorEvent(str, Enum):
    CONDITION_CHANGED = "CONDITION_CHANGED"
    CONFIDENCE_DROP = "CONFIDENCE_DROP"
    RISK_INCREASED = "RISK_INCREASED"
    STRUCTURE_CHANGED = "STRUCTURE_CHANGED"
    SCENARIO_INVALIDATED = "SCENARIO_INVALIDATED"
    APPROACHING_STOP = "APPROACHING_STOP"
    APPROACHING_TARGET = "APPROACHING_TARGET"
    TARGET_REACHED = "TARGET_REACHED"
    STOP_REACHED = "STOP_REACHED"


@dataclass(frozen=True)
class MonitorSnapshot:
    tracked_id: str
    captured_at: datetime
    confidence: float | None = None
    risk_score: float | None = None
    scenario_id: str | None = None
    state_hash: str | None = None


@dataclass(frozen=True)
class MonitorAlert:
    tracked_id: str
    event: MonitorEvent
    severity: str
    message_key: str
    dedupe_key: str
    snapshot: MonitorSnapshot


class SignalDecay:
    def __init__(self, half_life_seconds: float) -> None:
        if half_life_seconds <= 0:
            raise ValueError("half_life_seconds must be positive")
        self.half_life_seconds = half_life_seconds

    def factor(self, elapsed_seconds: float) -> float:
        if elapsed_seconds < 0:
            raise ValueError("elapsed_seconds cannot be negative")
        return 0.5 ** (elapsed_seconds / self.half_life_seconds)
