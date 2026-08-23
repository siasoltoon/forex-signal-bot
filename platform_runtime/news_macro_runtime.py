from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Sequence

import httpx


@dataclass(frozen=True)
class NewsEvent:
    event_id: str
    title: str
    published_at: datetime
    importance: str
    sentiment: float | None
    assets: tuple[str, ...]
    source: str


@dataclass(frozen=True)
class MacroEvent:
    event_id: str
    name: str
    timestamp: datetime
    importance: str
    actual: float | None
    forecast: float | None
    previous: float | None
    assets: tuple[str, ...]
    source: str


@dataclass(frozen=True)
class EventRisk:
    blocked: bool
    score: float
    reasons: tuple[str, ...]


class NewsProvider:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    async def fetch(self, query: str, limit: int = 20) -> tuple[NewsEvent, ...]:
        if not self.api_key:
            raise RuntimeError("NEWS_API_KEY is not configured")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get("https://newsapi.org/v2/everything", params={"q": query, "pageSize": limit, "apiKey": self.api_key, "language": "en"})
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
        return tuple(NewsEvent(str(item.get("url", index)), str(item.get("title", "")), datetime.fromisoformat(str(item["publishedAt"]).replace("Z", "+00:00")), "unknown", None, (), str(item.get("source", {}).get("name", "newsapi"))) for index, item in enumerate(payload.get("articles", [])))


class MacroProvider:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    async def fetch(self, series_id: str, limit: int = 20) -> tuple[MacroEvent, ...]:
        if not self.api_key:
            raise RuntimeError("FRED_API_KEY is not configured")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get("https://api.stlouisfed.org/fred/series/observations", params={"series_id": series_id, "api_key": self.api_key, "file_type": "json", "sort_order": "desc", "limit": limit})
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
        events = []
        for index, item in enumerate(payload.get("observations", [])):
            value = None if item.get("value") in {None, "."} else float(item["value"])
            events.append(MacroEvent(f"{series_id}:{index}", series_id, datetime.fromisoformat(item["date"]).replace(tzinfo=timezone.utc), "normal", value, None, None, (), "fred"))
        return tuple(events)


class EventRiskEngine:
    def evaluate(self, now: datetime, news: Sequence[NewsEvent] = (), macro: Sequence[MacroEvent] = (), lookahead_minutes: int = 30) -> EventRisk:
        reasons: list[str] = []
        score = 0.0
        for event in (*news, *macro):
            minutes = (event.published_at if isinstance(event, NewsEvent) else event.timestamp - now).total_seconds() / 60
            if isinstance(event, MacroEvent) and 0 <= minutes <= lookahead_minutes and event.importance in {"high", "critical"}:
                score = max(score, 1.0)
                reasons.append(f"high_impact_event:{event.name}")
        return EventRisk(score >= 1.0, score, tuple(reasons))


def configured_news_provider() -> NewsProvider:
    return NewsProvider(os.getenv("NEWS_API_KEY"))


def configured_macro_provider() -> MacroProvider:
    return MacroProvider(os.getenv("FRED_API_KEY"))
