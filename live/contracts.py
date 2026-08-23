from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SignalState(str, Enum):
    ACTIVE = "ACTIVE"
    WEAKENING = "WEAKENING"
    INVALIDATED = "INVALIDATED"
    TARGET_REACHED = "TARGET_REACHED"
    STOP_REACHED = "STOP_REACHED"
    CLOSED = "CLOSED"


@dataclass(frozen=True, slots=True)
class LiveSignal:
    signal_id: str
    symbol: str
    direction: str
    state: SignalState
    confidence: float
    entry: float | None = None
    stop_loss: float | None = None
    take_profit: tuple[float, ...] = ()
    last_update: str | None = None


@dataclass(frozen=True, slots=True)
class SignalUpdate:
    signal_id: str
    previous_state: SignalState
    current_state: SignalState
    reason: str
    severity: str = "normal"
    confidence: float | None = None


__all__ = ["LiveSignal", "SignalState", "SignalUpdate"]
