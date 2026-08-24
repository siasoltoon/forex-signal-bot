from telegram import Update
from telegram.ext import ContextTypes


async def back_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle back navigation."""

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "🤖 Forex AI Intelligence Platform\n\n"
            "به منوی اصلی برگشتید."
        )
