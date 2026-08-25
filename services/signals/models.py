from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class SignalStatus(str, Enum):
    ACTIVE = "ACTIVE"
    HIT_TP = "HIT_TP"
    HIT_SL = "HIT_SL"
    INVALIDATED = "INVALIDATED"
    EXPIRED = "EXPIRED"


@dataclass
class TradingSignal:
    symbol: str
    direction: str
    entry: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    confidence: float = 0.0
    status: SignalStatus = SignalStatus.ACTIVE
    invalidation_reason: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
