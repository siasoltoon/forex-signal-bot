from __future__ import annotations

from dataclasses import dataclass

from health import health_check
from telegram_bot.bot import create_bot


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

    telegram_bot: object | None = None

    def health(self) -> dict[str, str]:
        """
        Return application health information.
        """

        return health_check()

    def start(self) -> None:
        """
        Start the application.
        """

        status = self.health()

        print(
            f"{status['service']} "
            f"started successfully."
        )

    def init_telegram(self) -> None:
    """
    Initialize Telegram bot.
    """

    try:
        self.telegram_bot = create_bot()

    except ValueError:
        self.telegram_bot = None


def create_app() -> Application:
    """
    Application factory.
    """

    app = Application()

    app.init_telegram()

    return app
