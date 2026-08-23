from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class LiveSignalState:
    signal_id: str
    initial_confidence: float
    current_confidence: float
    created_at: datetime
    last_update: datetime
    invalidated: bool = False


@dataclass(frozen=True, slots=True)
class LiveSignalEvent:
    signal_id: str
    event: str
    severity: str
    confidence: float
    message: str


class LiveSignalMonitor:
    def update(
        self,
        state: LiveSignalState,
        *,
        now: datetime,
        current_confidence: float,
        invalidated: bool = False,
        approaching_stop: bool = False,
        approaching_target: bool = False,
    ) -> tuple[LiveSignalState, tuple[LiveSignalEvent, ...]]:
        if not 0 <= current_confidence <= 1:
            raise ValueError("current_confidence must be between 0 and 1")
        events: list[LiveSignalEvent] = []
        if invalidated and not state.invalidated:
            events.append(LiveSignalEvent(state.signal_id, "INVALIDATED", "CRITICAL", current_confidence, "scenario invalidated"))
        elif current_confidence < state.current_confidence - 0.15:
            events.append(LiveSignalEvent(state.signal_id, "CONFIDENCE_DROP", "IMPORTANT", current_confidence, "confidence dropped materially"))
        if approaching_stop:
            events.append(LiveSignalEvent(state.signal_id, "APPROACHING_STOP", "IMPORTANT", current_confidence, "price is approaching stop level"))
        if approaching_target:
            events.append(LiveSignalEvent(state.signal_id, "APPROACHING_TARGET", "NORMAL", current_confidence, "price is approaching target"))
        updated = LiveSignalState(state.signal_id, state.initial_confidence, current_confidence, state.created_at, now, invalidated)
        return updated, tuple(events)
