from __future__ import annotations

import logging

from telegram.ext import ContextTypes

from .tracker import list_tracking, refresh_tracking

logger = logging.getLogger(__name__)


async def refresh_all_tracked_signals(context: ContextTypes.DEFAULT_TYPE) -> None:
    bot = context.bot
    for user_id in {item.user_id for item in list(_all_tracked())}:
        for item in list_tracking(user_id):
            async def notify(text: str, uid: int = user_id) -> None:
                await bot.send_message(chat_id=uid, text=text, parse_mode="HTML")
            try:
                await refresh_tracking(item, notify)
            except Exception:
                logger.exception("Signal tracking refresh failed for user=%s symbol=%s", user_id, item.symbol)


def _all_tracked():
    # Kept local to avoid exposing mutable tracker internals outside this service.
    from .tracker import ACTIVE_TRACKS
    return list(ACTIVE_TRACKS.values())
