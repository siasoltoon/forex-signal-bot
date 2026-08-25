from __future__ import annotations

import asyncio

from services.base import BaseService

from .manager import SignalManager
from .monitor import SignalMonitor
from .pipeline import SignalPipeline


class SignalEngineService(BaseService):
    """Application service wrapper for the live signal engine."""

    name = "signal-engine"
    critical = False

    def __init__(self) -> None:
        self.manager = SignalManager()
        self.pipeline = SignalPipeline(self.manager)
        self.monitor = SignalMonitor(self.manager)
        self._monitor_task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        """Start live signal monitoring lifecycle."""
        if self._running:
            return

        self._running = True
        self._monitor_task = asyncio.create_task(
            self._monitor_loop()
        )

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
                self.monitor.check()
            except Exception:
                pass

            await asyncio.sleep(30)

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
