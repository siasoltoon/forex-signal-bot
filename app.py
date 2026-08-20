from __future__ import annotations

from dataclasses import dataclass

from health import health_check


@dataclass
class Application:
    """
    Main application container.

    This class will eventually coordinate:
    - Telegram bot
    - Market data
    - Analysis engines
    - AI
    - Risk management
    """

    name: str = "forex-signal-bot"

    def health(self) -> dict[str, str]:
        """
        Return application health information.
        """

        return health_check()

    def start(self) -> None:
        """
        Start the application.

        External services will be connected here
        in later stages.
        """

        status = self.health()

        print(
            f"{status['service']} "
            f"started successfully."
        )


def create_app() -> Application:
    """
    Application factory.
    """

    return Application()
