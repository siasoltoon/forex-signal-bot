from __future__ import annotations

import os

from app import create_app


def main() -> None:
    app = create_app()

    app.start()

    run_bot = os.getenv(
        "RUN_TELEGRAM_BOT",
        "false",
    ).lower() == "true"

    if run_bot and app.telegram_bot:
        app.telegram_bot.run_polling()


if __name__ == "__main__":
    main()
