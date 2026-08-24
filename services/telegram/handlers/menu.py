from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def analysis_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ تحلیل سریع", callback_data="analysis_quick")],
        [InlineKeyboardButton("📊 تحلیل کامل", callback_data="analysis_full")],
        [InlineKeyboardButton("🕒 تحلیل چند تایم‌فریمی", callback_data="analysis_mtf")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="home")],
    ])


def signal_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📡 سیگنال جدید", callback_data="signal_new")],
        [InlineKeyboardButton("📈 دنبال کردن سیگنال", callback_data="signal_track")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="home")],
    ])
