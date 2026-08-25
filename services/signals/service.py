from __future__ import annotations

import asyncio
import logging

from services.base import BaseService

from data.market_data import MarketDataEngine

from .manager import SignalManager
from .monitor import SignalMonitor
from .pipeline import SignalPipeline


logger = logging.getLogger(__name__)


class SignalEngineService(BaseService):
    """Application service wrapper for the live signal engine."""

    name = "signal-engine"
    critical = False

    def __init__(self, market_data: MarketDataEngine | None = None) -> None:
        self.manager = SignalManager()
        self.pipeline = SignalPipeline(self.manager)
        self.monitor = SignalMonitor(self.manager)
        self.market_data = market_data or MarketDataEngine()
        self._monitor_task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        """Start live signal monitoring lifecycle."""
        if self._running:
            return

        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop(self) -> None:
        """Stop live signal monitoring lifecycle safely."""
        self._running = False

        if self._monitor_task:
            self._monitor_task.cancel()

            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

            self._monitor_task = None

    async def _monitor_loop(self) -> None:
        while self._running:
            try:
                await self._check_active_signals()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.exception(
                    "Signal monitor cycle failed: %s",
                    exc,
                )

            await asyncio.sleep(30)

    async def _check_active_signals(self) -> None:
        for signal in self.manager.active_signals():
            try:
                price_data = await self.market_data.get_latest_oanda_price(
                    signal.symbol
                )

                if not price_data:
                    logger.warning(
                        "No price data available for signal %s",
                        signal.symbol,
                    )
                    continue

                price = float(price_data.get("close") or price_data.get("bid"))
                await self.monitor.check(signal.symbol, price)

            except Exception as exc:
                logger.exception(
                    "Signal check failed for %s: %s",
                    signal.symbol,
                    exc,
                )

    def create_signal(self, analysis_result, *, symbol: str, timeframe: str):
        """Create and register a live trading signal from analysis output."""
        return self.pipeline.create_and_register(
            analysis_result,
            symbol=symbol,
            timeframe=timeframe,
        )

    def health(self) -> dict[str, str]:
        return {
            "service": self.name,
            "status": "running",
            "signals": str(len(self.manager.active_signals())),
        }
