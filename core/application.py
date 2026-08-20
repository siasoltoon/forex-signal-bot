from __future__ import annotations

from dataclasses import dataclass, field

from core.service import ServiceManager
from health import health_check
from services.telegram.service import TelegramService


@dataclass
class Application:
    """
    Main application core.
    """


    name: str = "forex-signal-bot"


    services: ServiceManager = field(
        default_factory=ServiceManager
    )


    def health(self) -> dict:

        return {
            "application": health_check(),
            "services": self.services.health(),
        }


    async def start(self) -> None:
        """
        Start application.
        """

        await self.services.start_all()

        print(
            f"{self.name} started successfully."
        )


    async def stop(self) -> None:

        await self.services.stop_all()



def create_app() -> Application:

    app = Application()

    app.services.register(
        TelegramService()
    )

    return app
