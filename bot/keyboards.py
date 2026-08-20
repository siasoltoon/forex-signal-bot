from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_keyboard() -> InlineKeyboardMarkup:
    """
    Main interactive keyboard of the bot.
    """

    keyboard = [
        [
            InlineKeyboardButton(
                "📊 تحلیل بازار",
                callback_data="analyze",
            ),
        ],
        [
            InlineKeyboardButton(
                "⚙️ تنظیمات",
                callback_data="settings",
            ),
            InlineKeyboardButton(
                "📚 سبک‌های تحلیل",
                callback_data="styles",
            ),
        ],
        [
            InlineKeyboardButton(
                "ℹ️ راهنما",
                callback_data="help",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)
