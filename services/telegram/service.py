from __future__ import annotations

from services.base import BaseService

from services.telegram.client import TelegramClient
from services.telegram.config import TelegramConfig


class TelegramService(BaseService):
    """
    Telegram bot service.
    """

    name = "telegram"


    def __init__(self) -> None:

        self.config = TelegramConfig()

        self.client: TelegramClient | None = None


    async def start(self) -> None:
        """
        Start Telegram service.
        """

        if not self.config.enabled:

            print(
                "Telegram disabled: token missing."
            )

            return


        self.client = TelegramClient(
            self.config.token
        )


        await self.client.start()


    async def stop(self) -> None:
        """
        Stop Telegram service.
        """

        if self.client:

            await self.client.stop()


    def health(self) -> dict[str, str]:

        return {
            "service": self.name,
            "status": "running"
            if self.client
            else "disabled",
        }
