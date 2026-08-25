from __future__ import annotations

from telegram import BotCommand
from telegram.ext import Application

from core.logger import setup_logger
from services.telegram.router import register_routes


logger = setup_logger()


class TelegramClient:
    """Telegram bot client with explicit startup diagnostics."""

    def __init__(self, token: str, analysis_service=None, signal_engine=None) -> None:
        self.application = (
            Application
            .builder()
            .token(token)
            .build()
        )

        if analysis_service is not None:
            self.application.bot_data["analysis_service"] = analysis_service

        if signal_engine is not None:
            self.application.bot_data["signal_engine"] = signal_engine

        register_routes(self.application)
        logger.info("Telegram client configured and routes registered.")

    async def start(self) -> None:
        """Initialize the bot, validate the token and start polling."""
        logger.info("Starting Telegram client...")

        await self.application.initialize()
        logger.info("Telegram application initialized.")

        bot = self.application.bot
        me = await bot.get_me()
        logger.info(
            "Telegram authentication successful: @%s (id=%s).",
            me.username,
            me.id,
        )

        await bot.set_my_commands([
            BotCommand("start", "شروع ربات"),
            BotCommand("help", "راهنما"),
            BotCommand("signal", "دریافت سیگنال"),
            BotCommand("status", "وضعیت سیستم"),
            BotCommand("settings", "تنظیمات"),
        ])
        logger.info("Telegram commands registered.")

        await self.application.start()
        logger.info("Telegram application runtime started.")

        updater = self.application.updater
        if updater is None:
            raise RuntimeError("Telegram updater is unavailable; polling cannot start.")

        await updater.start_polling()
        logger.info("Telegram polling started successfully.")
        logger.info("Telegram bot is online.")

    async def stop(self) -> None:
        """Stop polling and shut down the Telegram application."""
        logger.info("Stopping Telegram client...")

        updater = self.application.updater
        if updater is not None and updater.running:
            await updater.stop()

        if self.application.running:
            await self.application.stop()

        await self.application.shutdown()
        logger.info("Telegram bot stopped.")
