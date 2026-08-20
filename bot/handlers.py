import logging

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from bot.keyboards import main_keyboard
from bot.messages import HELP_MESSAGE, WELCOME_MESSAGE


logger = logging.getLogger(__name__)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle /start."""

    if not update.message:
        return

    await update.message.reply_text(
        WELCOME_MESSAGE,
        reply_markup=main_keyboard(),
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle /help."""

    if not update.message:
        return

    await update.message.reply_text(
        HELP_MESSAGE,
    )


async def status_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle /status."""

    if not update.message:
        return

    await update.message.reply_text(
        "🟢 سیستم اصلی ربات فعال است.\n"
        "🧠 موتور تحلیل در حال توسعه است.",
    )


async def analyze_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle /analyze."""

    if not update.message:
        return

    await update.message.reply_text(
        "📊 موتور تحلیل بازار هنوز در حال ساخت است.\n\n"
        "در مراحل بعدی انتخاب نماد، تایم‌فریم و "
        "سبک‌های تحلیل به این بخش اضافه می‌شود.",
    )


async def settings_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle /settings."""

    if not update.message:
        return

    await update.message.reply_text(
        "⚙️ بخش تنظیمات در حال توسعه است.",
    )


async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle inline keyboard buttons."""

    query = update.callback_query

    if not query:
        return

    await query.answer()

    if query.data == "analyze":
        await query.message.reply_text(
            "📊 بخش تحلیل بازار انتخاب شد.\n\n"
            "موتور تحلیل در حال ساخت است.",
        )

    elif query.data == "settings":
        await query.message.reply_text(
            "⚙️ تنظیمات در نسخه‌های بعدی فعال می‌شود.",
        )

    elif query.data == "styles":
        await query.message.reply_text(
            "📚 سبک‌های تحلیلی:\n\n"
            "• Technical Analysis\n"
            "• Classical Price Action\n"
            "• Modern Price Action\n"
            "• Supply & Demand\n"
            "• Elliott Wave\n"
            "• Harmonic Trading\n"
            "• Time Analysis\n"
            "• Al Brooks\n"
            "• Lance Beggs",
        )

    elif query.data == "help":
        await query.message.reply_text(
            HELP_MESSAGE,
        )


def register_handlers(application) -> None:
    """Register all Telegram handlers."""

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    application.add_handler(
        CommandHandler("status", status_command)
    )

    application.add_handler(
        CommandHandler("analyze", analyze_command)
    )

    application.add_handler(
        CommandHandler("settings", settings_command)
    )

    application.add_handler(
        CallbackQueryHandler(button_handler)
    )
