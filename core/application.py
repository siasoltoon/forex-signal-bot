from __future__ import annotations

from dataclasses import dataclass, field

from core.service import ServiceManager
from health import health_check


@dataclass
class Application:
    """
    Main application container.
    """

    name: str = "forex-signal-bot"

    services: ServiceManager = field(
        default_factory=ServiceManager
    )


    def health(self) -> dict:
        """
        Return application health.
        """

        return {
            "application": health_check(),
            "services": self.services.health(),
        }


    def start(self) -> None:
        """
        Start application services.
        """

        self.services.start_all()

        print(
            f"{self.name} started successfully."
        )


    def stop(self) -> None:
        """
        Stop application services.
        """

        self.services.stop_all()



def create_app() -> Application:
    """
    Application factory.
    """

    app = Application()

    return app
