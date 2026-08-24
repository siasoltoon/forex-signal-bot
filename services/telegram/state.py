from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class TelegramUserState:
    user_id: int
    current_menu: str = "home"
    language: str = "fa"
    settings: Dict[str, Any] = field(default_factory=dict)


USER_STATES: Dict[int, TelegramUserState] = {}


def get_user_state(user_id: int) -> TelegramUserState:
    if user_id not in USER_STATES:
        USER_STATES[user_id] = TelegramUserState(user_id=user_id)
    return USER_STATES[user_id]


def update_menu(user_id: int, menu: str) -> TelegramUserState:
    state = get_user_state(user_id)
    state.current_menu = menu
    return state
