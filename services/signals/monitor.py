from __future__ import annotations

from .manager import SignalManager


class SignalMonitor:
    """Placeholder for market-driven signal validation and updates."""

    def __init__(self, manager: SignalManager) -> None:
        self.manager = manager

    async def check(self, symbol: str, price: float) -> dict:
        signal = self.manager.get(symbol)
        if not signal:
            return {"status": "NOT_FOUND"}

        return {
            "symbol": symbol,
            "status": signal.status.value,
            "price": price,
        }
