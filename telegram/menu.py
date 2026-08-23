from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MenuItem:
    key: str
    label_key: str
    command: str | None = None


MAIN_MENU: tuple[MenuItem, ...] = (
    MenuItem("analysis", "menu.analysis", "/analysis"),
    MenuItem("market", "menu.market", "/market"),
    MenuItem("scanner", "menu.scanner", "/scanner"),
    MenuItem("portfolio", "menu.portfolio", "/portfolio"),
    MenuItem("journal", "menu.journal", "/journal"),
    MenuItem("backtest", "menu.backtest", "/backtest"),
    MenuItem("settings", "menu.settings", "/settings"),
    MenuItem("status", "menu.status", "/status"),
)
