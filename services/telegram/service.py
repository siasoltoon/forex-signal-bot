from __future__ import annotations

from services.base import BaseService

from services.telegram.client import TelegramClient
from services.telegram.config import TelegramConfig


class TelegramService(BaseService):
    """
    Telegram application service.
    """

    name = "telegram"


    def __init__(self) -> None:

        self.config = TelegramConfig()

        self.client: TelegramClient | None = None


    def start(self) -> None:

        if not self.config.enabled:

            print(
                "Telegram disabled: token missing."
            )

            return


        self.client = TelegramClient(
            self.config.token
        )


        print(
            "Telegram service ready."
        )


    def stop(self) -> None:

        if self.client:

            print(
                "Stopping Telegram service."
            )


    def health(self) -> dict[str, str]:

        return {
            "service": self.name,
            "status": "ready",
        }
