from __future__ import annotations

from dataclasses import dataclass, field

from config.settings import Settings
from core.logger import setup_logger
from core.service import ServiceManager
from core.health_server import HealthServer

from health import health_check

from services.telegram.service import TelegramService
from services.worker.service import WorkerProcessingService


logger = setup_logger()


@dataclass
class Application:
    """Main application core."""

    name: str = "forex-signal-bot"

    services: ServiceManager = field(default_factory=ServiceManager)

    health_server: HealthServer = field(init=False)

    def __post_init__(self) -> None:
        configuration = Settings.load()
        self.health_server = HealthServer(
            self.health,
            host=configuration.health_host,
            port=configuration.health_port,
        )

        self.services.register(TelegramService())
        worker_service = WorkerProcessingService.from_settings()
        self.services.register(worker_service)
        set_gateway = getattr(self.health_server, "set_worker_gateway", None)
        if callable(set_gateway):
            set_gateway(getattr(worker_service, "gateway", None))

    def health(self) -> dict:
        application_health = health_check()
        service_health = self.services.health()

        critical_failures = [
            name
            for name, status in service_health.items()
            if status.get("critical") and status.get("status") != "ok"
        ]

        if critical_failures:
            application_health = {
                **application_health,
                "status": "degraded",
                "critical_failures": critical_failures,
            }

        return {
            "application": application_health,
            "services": service_health,
        }

    async def start(self) -> None:
        """Start the health endpoint before application services."""

        try:
            self.health_server.start()
            await self.services.start_all()
        except Exception:
            try:
                self.health_server.stop()
            finally:
                await self.services.stop_all()
            raise

        logger.info(f"{self.name} started successfully.")

    async def stop(self) -> None:
        """Stop application."""

        try:
            self.health_server.stop()
        finally:
            await self.services.stop_all()

        logger.info(f"{self.name} stopped successfully.")


def create_app() -> Application:
    """Application factory."""

    return Application()
