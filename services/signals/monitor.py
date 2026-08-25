from __future__ import annotations

from .manager import SignalManager
from .models import SignalStatus


class SignalMonitor:
    """Market-driven signal validation and lifecycle updates."""

    def __init__(self, manager: SignalManager) -> None:
        self.manager = manager

    def _invalidate(self, symbol: str, reason: str):
        signal = self.manager.get(symbol)
        if not signal:
            return None

        signal.invalidation_reason = reason
        return self.manager.update_status(symbol, SignalStatus.INVALIDATED)

    async def check(self, symbol: str, price: float) -> dict:
        signal = self.manager.get(symbol)
        if not signal:
            return {"status": "NOT_FOUND"}

        if signal.status != SignalStatus.ACTIVE:
            return {
                "symbol": symbol,
                "status": signal.status.value,
                "price": price,
                "reason": signal.invalidation_reason,
            }

        direction = str(signal.direction).upper()

        if signal.take_profit is not None:
            if direction in {"BUY", "LONG"} and price >= signal.take_profit:
                signal = self.manager.update_status(symbol, SignalStatus.HIT_TP)
            elif direction in {"SELL", "SHORT"} and price <= signal.take_profit:
                signal = self.manager.update_status(symbol, SignalStatus.HIT_TP)

        if signal and signal.status == SignalStatus.ACTIVE and signal.stop_loss is not None:
            if direction in {"BUY", "LONG"} and price <= signal.stop_loss:
                signal = self.manager.update_status(symbol, SignalStatus.HIT_SL)
            elif direction in {"SELL", "SHORT"} and price >= signal.stop_loss:
                signal = self.manager.update_status(symbol, SignalStatus.HIT_SL)

        if signal and signal.status == SignalStatus.ACTIVE and signal.entry is not None:
            if direction in {"BUY", "LONG"} and price < signal.entry * 0.97:
                signal = self._invalidate(symbol, "market_moved_against_entry")
            elif direction in {"SELL", "SHORT"} and price > signal.entry * 1.03:
                signal = self._invalidate(symbol, "market_moved_against_entry")

        return {
            "symbol": symbol,
            "status": signal.status.value if signal else SignalStatus.INVALIDATED.value,
            "price": price,
            "reason": signal.invalidation_reason if signal else "unknown",
        }
