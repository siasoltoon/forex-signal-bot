from __future__ import annotations

from .models import SignalStatus, TradingSignal


class SignalManager:
    """Manage signal lifecycle without coupling to Telegram or analysis engines."""

    def __init__(self) -> None:
        self._signals: dict[str, TradingSignal] = {}

    def register(self, signal: TradingSignal) -> TradingSignal:
        self._signals[signal.symbol] = signal
        return signal

    def get(self, symbol: str) -> TradingSignal | None:
        return self._signals.get(symbol)

    def update_status(self, symbol: str, status: SignalStatus) -> TradingSignal | None:
        signal = self._signals.get(symbol)
        if signal:
            signal.status = status
        return signal

    def active_signals(self) -> list[TradingSignal]:
        return [
            signal
            for signal in self._signals.values()
            if signal.status == SignalStatus.ACTIVE
        ]
