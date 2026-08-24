from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


@dataclass(frozen=True, slots=True)
class UserContext:
    user_id: str
    language: str = "fa"
    authenticated: bool = True


@dataclass(frozen=True, slots=True)
class CommandRequest:
    command: str
    args: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CallbackRequest:
    action: str
    payload: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class BotResponse:
    text: str
    buttons: tuple[tuple[str, str], ...] = ()
    parse_mode: str | None = None


class CommandHandler(Protocol):
    def handle(self, request: CommandRequest, context: UserContext) -> BotResponse: ...


class CallbackHandler(Protocol):
    def handle(self, request: CallbackRequest, context: UserContext) -> BotResponse: ...
