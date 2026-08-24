from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Sequence


class TradeState(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    TP = "tp"
    SL = "sl"
    INVALIDATED = "invalidated"
    CLOSED = "closed"


@dataclass(frozen=True)
class LiveSignal:
    signal_id: str
    symbol: str
    side: str
    entry: float
    stop: float
    targets: tuple[float, ...]
    confidence: float
    scenario_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class LiveEvent:
    signal_id: str
    kind: str
    severity: str
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AlertEngine:
    def __init__(self) -> None:
        self._sent: set[tuple[str, str]] = set()

    def emit(self, event: LiveEvent) -> LiveEvent | None:
        key = (event.signal_id, event.kind)
        if key in self._sent:
            return None
        self._sent.add(key)
        return event


class TradeLifecycle:
    def __init__(self, signal: LiveSignal) -> None:
        self.signal = signal
        self.state = TradeState.PLANNED
        self.last_price: float | None = None

    def update(self, price: float, scenario_valid: bool = True) -> tuple[LiveEvent, ...]:
        self.last_price = price
        side = self.signal.side.upper()
        events: list[LiveEvent] = []
        if not scenario_valid and self.state not in {TradeState.CLOSED, TradeState.INVALIDATED}:
            self.state = TradeState.INVALIDATED
            events.append(LiveEvent(self.signal.signal_id, "scenario_invalidated", "critical", "سناریو ابطال شد"))
            return tuple(events)
        if self.state == TradeState.PLANNED:
            if (side == "BUY" and price >= self.signal.entry) or (side == "SELL" and price <= self.signal.entry):
                self.state = TradeState.ACTIVE
                events.append(LiveEvent(self.signal.signal_id, "activated", "normal", "شرایط ورود فعال شد"))
        if self.state == TradeState.ACTIVE:
            stop_hit = price <= self.signal.stop if side == "BUY" else price >= self.signal.stop
            target_hit = any(price >= target for target in self.signal.targets) if side == "BUY" else any(price <= target for target in self.signal.targets)
            if stop_hit:
                self.state = TradeState.SL
                events.append(LiveEvent(self.signal.signal_id, "sl", "critical", "حد ضرر فعال شد"))
            elif target_hit:
                self.state = TradeState.TP
                events.append(LiveEvent(self.signal.signal_id, "tp", "important", "هدف قیمتی فعال شد"))
        return tuple(events)


class LiveMonitor:
    def __init__(self, alert_engine: AlertEngine | None = None) -> None:
        self.alerts = alert_engine or AlertEngine()
        self._watchers: dict[str, TradeLifecycle] = {}
        self._callbacks: list[Callable[[LiveEvent], None]] = []

    def register(self, signal: LiveSignal) -> None:
        self._watchers[signal.signal_id] = TradeLifecycle(signal)

    def subscribe(self, callback: Callable[[LiveEvent], None]) -> None:
        self._callbacks.append(callback)

    def update(self, signal_id: str, price: float, scenario_valid: bool = True) -> tuple[LiveEvent, ...]:
        lifecycle = self._watchers[signal_id]
        emitted = []
        for event in lifecycle.update(price, scenario_valid):
            unique = self.alerts.emit(event)
            if unique:
                emitted.append(unique)
                for callback in self._callbacks:
                    callback(unique)
        return tuple(emitted)

    def active(self) -> Sequence[TradeLifecycle]:
        return tuple(self._watchers.values())
