from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


async def start_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle /start command with main menu.
    """

    keyboard = [
        [
            InlineKeyboardButton("📊 تحلیل هوشمند", callback_data="analysis"),
            InlineKeyboardButton("📡 سیگنال زنده", callback_data="signals"),
        ],
        [
            InlineKeyboardButton("🔎 اسکن بازار", callback_data="scanner"),
            InlineKeyboardButton("🧠 AI Coach", callback_data="coach"),
        ],
        [
            InlineKeyboardButton("📒 ژورنال معاملات", callback_data="journal"),
            InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings"),
        ],
    ]

    if update.message:
        await update.message.reply_text(
            "🤖 Forex AI Intelligence Platform\n\n"
            "سلام 👋\n\n"
            "ربات آماده است. یکی از بخش‌ها را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
