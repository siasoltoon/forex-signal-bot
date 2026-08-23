from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class AnalysisSession:
    user_id: str
    market: str | None = None
    symbol: str | None = None
    timeframes: tuple[str, ...] = ()
    styles: tuple[str, ...] = ()
    mode: str = "smart"
    session_id: str = field(default_factory=lambda: uuid4().hex)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def set_market(self, market: str, symbol: str) -> None:
        self.market, self.symbol = market, symbol

    def set_timeframes(self, *timeframes: str) -> None:
        self.timeframes = tuple(dict.fromkeys(timeframes))

    def set_styles(self, *styles: str) -> None:
        self.styles = tuple(dict.fromkeys(styles))

    def snapshot(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "market": self.market,
            "symbol": self.symbol,
            "timeframes": self.timeframes,
            "styles": self.styles,
            "mode": self.mode,
        }
