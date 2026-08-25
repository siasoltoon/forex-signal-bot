from __future__ import annotations

from dataclasses import dataclass, field

from core.logger import setup_logger
from core.service import ServiceManager

from health import health_check

from services.telegram.service import TelegramService
from services.analysis.service import AnalysisService
from services.signals.service import SignalEngineService


logger = setup_logger()


@dataclass
class Application:
    """Main application core."""

    name: str = "forex-signal-bot"
    services: ServiceManager = field(default_factory=ServiceManager)

    def health(self) -> dict:
        return {
            "application": health_check(),
            "services": self.services.health(),
        }

    async def start(self) -> None:
        await self.services.start_all()
        logger.info(f"{self.name} started successfully.")

    async def stop(self) -> None:
        await self.services.stop_all()
        logger.info(f"{self.name} stopped successfully.")


def create_app() -> Application:
    app = Application()

    analysis_service = AnalysisService()
    signal_engine_service = SignalEngineService()

    app.services.register(
        analysis_service
    )

    app.services.register(
        signal_engine_service
    )

    app.services.register(
        TelegramService(analysis_service=analysis_service)
    )

    return app
