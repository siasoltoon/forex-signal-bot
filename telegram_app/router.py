from __future__ import annotations

from collections.abc import Callable

from .contracts import BotResponse, CallbackHandler, CallbackRequest, CommandHandler, CommandRequest, UserContext


class TelegramRouter:
    def __init__(self) -> None:
        self._commands: dict[str, CommandHandler] = {}
        self._callbacks: dict[str, CallbackHandler] = {}

    def register_command(self, command: str, handler: CommandHandler) -> None:
        self._commands[command.lstrip("/").lower()] = handler

    def register_callback(self, action: str, handler: CallbackHandler) -> None:
        self._callbacks[action] = handler

    def dispatch_command(self, request: CommandRequest, context: UserContext) -> BotResponse:
        handler = self._commands.get(request.command.lstrip("/").lower())
        if handler is None:
            return BotResponse("دستور ناشناخته است.")
        return handler.handle(request, context)

    def dispatch_callback(self, request: CallbackRequest, context: UserContext) -> BotResponse:
        handler = self._callbacks.get(request.action)
        if handler is None:
            return BotResponse("عملیات ناشناخته است.")
        return handler.handle(request, context)
