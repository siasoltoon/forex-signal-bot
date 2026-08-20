from __future__ import annotations

from telegram.ext import Application

from core.logger import setup_logger
from services.telegram.router import register_routes


logger = setup_logger()


class TelegramClient:
    """
    Telegram bot client.
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


    async def start(self) -> None:
        """
        Start telegram bot.
        """

        await self.application.initialize()

        await self.application.start()

        if self.application.updater:

            await self.application.updater.start_polling()


        logger.info(
            "Telegram bot is online."
        )


    async def stop(self) -> None:
        """
        Stop telegram bot.
        """

        if self.application.updater:

            await self.application.updater.stop()


        await self.application.stop()

        await self.application.shutdown()


        logger.info(
            "Telegram bot stopped."
        )
