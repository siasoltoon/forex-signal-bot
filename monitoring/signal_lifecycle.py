from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class LifecycleState(StrEnum):
    ACTIVE = "ACTIVE"
    WEAKENING = "WEAKENING"
    INVALIDATED = "INVALIDATED"
    TARGET_REACHED = "TARGET_REACHED"
    STOP_REACHED = "STOP_REACHED"
    CLOSED = "CLOSED"


@dataclass(frozen=True, slots=True)
class SignalSnapshot:
    signal_id: str
    direction: str
    confidence: float
    state: LifecycleState = LifecycleState.ACTIVE


@dataclass(frozen=True, slots=True)
class LifecycleUpdate:
    previous: SignalSnapshot
    current: SignalSnapshot
    changed: bool
    severity: str


class SignalLifecycle:
    def update(self, previous: SignalSnapshot, *, confidence: float, invalidated: bool = False, target_reached: bool = False, stop_reached: bool = False) -> LifecycleUpdate:
        confidence = max(0.0, min(1.0, confidence))
        if stop_reached:
            state = LifecycleState.STOP_REACHED
        elif target_reached:
            state = LifecycleState.TARGET_REACHED
        elif invalidated:
            state = LifecycleState.INVALIDATED
        elif confidence < previous.confidence and confidence < 0.5:
            state = LifecycleState.WEAKENING
        else:
            state = previous.state
        current = SignalSnapshot(previous.signal_id, previous.direction, confidence, state)
        changed = current != previous
        severity = "CRITICAL" if state in {LifecycleState.INVALIDATED, LifecycleState.STOP_REACHED} else "IMPORTANT" if changed else "NORMAL"
        return LifecycleUpdate(previous, current, changed, severity)
