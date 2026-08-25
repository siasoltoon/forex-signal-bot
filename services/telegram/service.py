from __future__ import annotations

from services.base import BaseService

from core.logger import setup_logger
from services.telegram.client import TelegramClient
from services.telegram.config import TelegramConfig
from services.analysis.service import AnalysisService
from services.signals.service import SignalEngineService


logger = setup_logger()


class TelegramService(BaseService):
    """Telegram bot service."""

    name = "telegram"
    critical = True

    def __init__(
        self,
        analysis_service: AnalysisService | None = None,
        signal_engine: SignalEngineService | None = None,
    ) -> None:
        self.config = TelegramConfig()
        self.client: TelegramClient | None = None
        self.analysis_service = analysis_service
        self.signal_engine = signal_engine

    async def start(self) -> None:
        """Start the Telegram service and fail loudly if it cannot connect."""
        logger.info("Starting Telegram service...")

        if not self.config.enabled:
            raise RuntimeError("Telegram is disabled because TELEGRAM_BOT_TOKEN is missing.")

        self.client = TelegramClient(
            self.config.token,
            analysis_service=self.analysis_service,
            signal_engine=self.signal_engine,
        )
        await self.client.start()

        logger.info("Telegram service started successfully.")

    async def stop(self) -> None:
        """Stop the Telegram service."""
        if self.client:
            await self.client.stop()

        logger.info("Telegram service stopped.")

    def health(self) -> dict[str, str]:
        """Return Telegram service health information."""
        return {
            "service": self.name,
            "status": "running" if self.client else "stopped",
            "critical": str(self.critical).lower(),
        }
