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

class SignalMonitor:
    def update(self, direction: str, price: float, entry: float, stop: float, target: float, confidence: float) -> SignalSnapshot:
        if direction == "BULLISH":
            if price <= stop: return SignalSnapshot(SignalState.STOPPED, confidence, "stop reached")
            if price >= target: return SignalSnapshot(SignalState.TARGET_REACHED, confidence, "target reached")
            if confidence < .35: return SignalSnapshot(SignalState.WEAKENING, confidence, "confidence degraded")
        if direction == "BEARISH":
            if price >= stop: return SignalSnapshot(SignalState.STOPPED, confidence, "stop reached")
            if price <= target: return SignalSnapshot(SignalState.TARGET_REACHED, confidence, "target reached")
            if confidence < .35: return SignalSnapshot(SignalState.WEAKENING, confidence, "confidence degraded")
        return SignalSnapshot(SignalState.ACTIVE, confidence, "signal remains valid")
