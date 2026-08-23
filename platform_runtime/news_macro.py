from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class NewsEvent:
    event_id: str
    source: str
    title: str
    published_at: str
    importance: str
    assets: tuple[str, ...]
    sentiment: float | None = None


@dataclass(frozen=True)
class MacroEvent:
    event_id: str
    name: str
    scheduled_at: str
    country: str
    importance: str
    affected_assets: tuple[str, ...]
    actual: float | None = None
    forecast: float | None = None
    previous: float | None = None


class NewsProvider(Protocol):
    async def fetch(self, asset: str) -> Sequence[NewsEvent]: ...


class MacroProvider(Protocol):
    async def fetch(self, asset: str) -> Sequence[MacroEvent]: ...


class EventRiskEngine:
    def assess(self, news: Sequence[NewsEvent], macro: Sequence[MacroEvent]) -> tuple[str, ...]:
        reasons: list[str] = []
        if any(e.importance.lower() in {"high", "critical"} for e in news):
            reasons.append("high_impact_news")
        if any(e.importance.lower() in {"high", "critical"} for e in macro):
            reasons.append("high_impact_macro_event")
        return tuple(dict.fromkeys(reasons))
