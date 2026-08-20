from __future__ import annotations

from services.base import BaseService

from core.logger import setup_logger
from services.telegram.client import TelegramClient
from services.telegram.config import TelegramConfig


logger = setup_logger()


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
        Start telegram service.
        """

        if not self.config.enabled:

            logger.warning(
                "Telegram disabled: token missing."
            )

            return


        self.client = TelegramClient(
            self.config.token
        )


        await self.client.start()


        logger.info(
            "Telegram service started."
        )


    async def stop(self) -> None:
        """
        Stop telegram service.
        """

        if self.client:

            await self.client.stop()


        logger.info(
            "Telegram service stopped."
        )


    def health(self) -> dict[str, str]:
        """
        Telegram service health.
        """

        return {
            "service": self.name,
            "status": (
                "running"
                if self.client
                else "disabled"
            ),
        }
