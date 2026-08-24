from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class RecordState(StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


@dataclass(frozen=True, slots=True)
class UserRecord:
    user_id: str
    language: str = "fa"
    risk_percent: float = 1.0
    report_level: str = "advanced"
    notifications_enabled: bool = True
    favorite_markets: tuple[str, ...] = ()
    favorite_symbols: tuple[str, ...] = ()
    favorite_timeframes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AnalysisRecord:
    analysis_id: str
    user_id: str
    market: str
    symbol: str
    timeframe: str
    decision: str
    confidence: float | None
    created_at: datetime
    state: RecordState = RecordState.ACTIVE
    trace_id: str | None = None


@dataclass(frozen=True, slots=True)
class SignalRecord:
    signal_id: str
    analysis_id: str
    user_id: str
    decision: str
    entry: float | None
    stop_loss: float | None
    take_profit: float | None
    created_at: datetime
    status: str = "OPEN"


@dataclass(frozen=True, slots=True)
class JobRecord:
    job_id: str
    job_type: str
    priority: str
    status: str
    created_at: datetime
    worker_id: str | None = None
    retry_count: int = 0
    result: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TradeRecord:
    trade_id: str
    user_id: str
    signal_id: str | None
    symbol: str
    side: str
    entry: float
    exit: float | None
    quantity: float
    pnl: float | None
    created_at: datetime
    closed_at: datetime | None = None
