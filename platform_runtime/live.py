from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable


class TradeState(str, Enum):
    CREATED = "created"
    ACTIVE = "active"
    TP_HIT = "tp_hit"
    SL_HIT = "sl_hit"
    INVALIDATED = "invalidated"
    CLOSED = "closed"


@dataclass(frozen=True)
class LiveSignal:
    signal_id: str
    symbol: str
    direction: str
    entry: float
    stop: float | None = None
    target: float | None = None
    confidence: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class LiveEvent:
    signal_id: str
    kind: str
    severity: str
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class LiveMonitor:
    def __init__(self, on_event: Callable[[LiveEvent], None] | None = None) -> None:
        self.signals: dict[str, LiveSignal] = {}
        self.states: dict[str, TradeState] = {}
        self._last_event: dict[tuple[str, str], datetime] = {}
        self.on_event = on_event

    def register(self, signal: LiveSignal) -> None:
        self.signals[signal.signal_id] = signal
        self.states[signal.signal_id] = TradeState.CREATED

    def update(self, signal_id: str, price: float, confidence: float | None = None, invalidated: bool = False) -> list[LiveEvent]:
        signal = self.signals[signal_id]
        events: list[LiveEvent] = []
        if invalidated:
            self.states[signal_id] = TradeState.INVALIDATED
            events.append(LiveEvent(signal_id, "scenario_invalidated", "critical", "سناریو باطل شد"))
        elif signal.stop is not None and ((signal.direction == "BUY" and price <= signal.stop) or (signal.direction == "SELL" and price >= signal.stop)):
            self.states[signal_id] = TradeState.SL_HIT
            events.append(LiveEvent(signal_id, "stop_loss", "critical", "حد ضرر فعال شد"))
        elif signal.target is not None and ((signal.direction == "BUY" and price >= signal.target) or (signal.direction == "SELL" and price <= signal.target)):
            self.states[signal_id] = TradeState.TP_HIT
            events.append(LiveEvent(signal_id, "take_profit", "important", "حد سود فعال شد"))
        elif confidence is not None and confidence < signal.confidence - 15:
            events.append(LiveEvent(signal_id, "confidence_drop", "important", "میزان اطمینان کاهش یافته است"))
        for event in events:
            key = (event.signal_id, event.kind)
            if key not in self._last_event:
                self._last_event[key] = event.timestamp
                if self.on_event:
                    self.on_event(event)
            else:
                events.remove(event)
        return events
