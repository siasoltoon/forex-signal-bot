from __future__ import annotations

from application.session import AnalysisSession
from .contracts import BotResponse, CommandHandler, CommandRequest, UserContext
from .keyboards import analysis_menu, main_menu


class StartHandler(CommandHandler):
    def handle(self, request: CommandRequest, context: UserContext) -> BotResponse:
        return main_menu(context.language)


class HelpHandler(CommandHandler):
    def handle(self, request: CommandRequest, context: UserContext) -> BotResponse:
        text = "دستورات: /start /help /settings /language /analysis /market /scanner /portfolio /journal /backtest /status"
        if context.language == "en":
            text = "Commands: /start /help /settings /language /analysis /market /scanner /portfolio /journal /backtest /status"
        return BotResponse(text)


class AnalysisHandler(CommandHandler):
    def __init__(self, sessions: dict[str, AnalysisSession]) -> None:
        self._sessions = sessions

    def handle(self, request: CommandRequest, context: UserContext) -> BotResponse:
        self._sessions.setdefault(context.user_id, AnalysisSession(context.user_id))
        return analysis_menu(context.language)
