from __future__ import annotations

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

    def start(self) -> None:
        """Initialize signal engine resources."""
        return None

    def stop(self) -> None:
        """Release signal engine resources."""
        return None

    def health(self) -> dict[str, str]:
        return {
            "service": self.name,
            "status": "running",
            "signals": str(len(self.manager.active_signals())),
        }
