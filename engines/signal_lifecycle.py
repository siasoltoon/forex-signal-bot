from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SignalState(str, Enum):
    ACTIVE = "ACTIVE"
    WEAKENING = "WEAKENING"
    INVALIDATED = "INVALIDATED"
    TARGET_REACHED = "TARGET_REACHED"
    STOPPED = "STOPPED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True, slots=True)
class SignalSnapshot:
    state: SignalState
    confidence: float
    reason: str


class SignalLifecycleEngine:
    def evaluate(self, initial_direction: str, current_direction: str, initial_confidence: float, current_confidence: float, invalidated: bool = False, target_reached: bool = False, stopped: bool = False) -> SignalSnapshot:
        if stopped:
            return SignalSnapshot(SignalState.STOPPED, 0.0, "stop condition reached")
        if target_reached:
            return SignalSnapshot(SignalState.TARGET_REACHED, max(0.0, min(1.0, current_confidence)), "target condition reached")
        if invalidated or (initial_direction != current_direction and current_direction != "NEUTRAL"):
            return SignalSnapshot(SignalState.INVALIDATED, max(0.0, min(1.0, current_confidence)), "direction or invalidation changed")
        confidence = max(0.0, min(1.0, current_confidence))
        if confidence < max(0.0, initial_confidence * 0.7):
            return SignalSnapshot(SignalState.WEAKENING, confidence, "confidence decayed materially")
        return SignalSnapshot(SignalState.ACTIVE, confidence, "signal remains valid")
