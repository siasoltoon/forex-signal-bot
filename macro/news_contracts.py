from __future__ import annotations
from dataclasses import dataclass
from macro.event_contracts import EventImpact

@dataclass(frozen=True, slots=True)
class NewsItem:
    id: str
    timestamp: int
    title: str
    source: str
    impact: EventImpact
    sentiment: float | None = None
    assets: tuple[str, ...] = ()

class NewsImpactAggregator:
    def score(self, items: tuple[NewsItem, ...], asset: str) -> float:
        relevant = [x for x in items if asset in x.assets and x.sentiment is not None]
        if not relevant:
            return 0.0
        return sum(float(x.sentiment) for x in relevant) / len(relevant)
