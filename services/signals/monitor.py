from __future__ import annotations

from .manager import SignalManager
from .models import SignalStatus


class SignalMonitor:
    """Market-driven signal validation and lifecycle updates."""

    def __init__(self, manager: SignalManager) -> None:
        self.manager = manager

    async def check(self, symbol: str, price: float) -> dict:
        signal = self.manager.get(symbol)
        if not signal:
            return {"status": "NOT_FOUND"}

        if signal.status != SignalStatus.ACTIVE:
            return {
                "symbol": symbol,
                "status": signal.status.value,
                "price": price,
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

        return {
            "symbol": symbol,
            "status": signal.status.value if signal else SignalStatus.INVALIDATED.value,
            "price": price,
        }
