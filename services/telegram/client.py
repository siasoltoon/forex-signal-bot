from __future__ import annotations

from telegram.ext import Application


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


    def start(self) -> None:
        """
        Start telegram client.
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
