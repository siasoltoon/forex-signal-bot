from telegram_bot.bot import get_bot_token


def test_telegram_token_function_exists():
    assert callable(get_bot_token)
