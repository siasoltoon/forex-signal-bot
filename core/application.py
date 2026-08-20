from __future__ import annotations

from dataclasses import dataclass, field

from core.container import ServiceContainer
from core.logger import setup_logger
from health import health_check


@dataclass
class Application:
    """
    Main application core.

    Responsible for:
    - Service management
    - Application lifecycle
    - System health
    - Future module integration
    """

    name: str = "forex-signal-bot"

    container: ServiceContainer = field(
        default_factory=ServiceContainer
    )

    logger = field(
        default=None,
        init=False
    )


    def initialize(self) -> None:
        """
        Initialize application services.
        """

        self.logger = setup_logger()

        self.logger.info(
            "Initializing application..."
        )

        self.container.register(
            "health",
            health_check
        )


        self.logger.info(
            "Application initialized."
        )


    def health(self) -> dict[str, str]:
        """
        Return application health status.
        """

        health_service = self.container.get(
            "health"
        )

        return health_service()


    def start(self) -> None:
        """
        Start application.
        """

        self.initialize()

        status = self.health()

        self.logger.info(
            f"{status['service']} started successfully."
        )


    def stop(self) -> None:
        """
        Shutdown application.
        """

        if self.logger:

            self.logger.info(
                "Application stopped."
            )
