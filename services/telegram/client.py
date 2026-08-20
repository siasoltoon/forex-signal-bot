from __future__ import annotations

from telegram.ext import Application

from services.telegram.router import register_routes


class TelegramClient:
    """
    Telegram bot client wrapper.
    """


    def __init__(
        self,
        token: str,
    ) -> None:

        self.application = (
            Application
            .builder()
            .token(token)
            .build()
        )

        register_routes(
            self.application
        )


    def start(self) -> None:
        """
        Initialize telegram client.
        """

        print(
            "Telegram client initialized."
        )


    def stop(self) -> None:
        """
        Stop telegram client.
        """

        print(
            "Telegram client stopped."
        )
