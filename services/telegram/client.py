from __future__ import annotations

from telegram.ext import Application

from services.telegram.router import register_routes


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
        Start polling.
        """

        await self.application.initialize()

        await self.application.start()

        await self.application.updater.start_polling()


        print(
            "Telegram bot is online."
        )


    async def stop(self) -> None:

        await self.application.updater.stop()

        await self.application.stop()

        await self.application.shutdown()


        print(
            "Telegram bot stopped."
        )
