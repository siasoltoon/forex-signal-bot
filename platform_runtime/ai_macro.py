from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class ModelOutput:
    model: str
    label: str
    score: float
    uncertainty: float


class Model(Protocol):
    name: str
    async def predict(self, features: dict) -> ModelOutput: ...


class ModelRegistry:
    def __init__(self, models: Sequence[Model] = ()) -> None:
        self._models = {model.name: model for model in models}

    def register(self, model: Model) -> None:
        if model.name in self._models:
            raise ValueError(f"model already registered: {model.name}")
        self._models[model.name] = model

    def names(self) -> tuple[str, ...]:
        return tuple(self._models)


@dataclass(frozen=True)
class MacroEvent:
    name: str
    importance: str
    scheduled_at: str
    assets: tuple[str, ...] = ()


class EventRiskEngine:
    def assess(self, events: Sequence[MacroEvent], now_iso: str) -> tuple[bool, tuple[str, ...]]:
        # Event providers own timestamp semantics; this layer only carries explicit risk flags.
        critical = tuple(event.name for event in events if event.importance.lower() in {"high", "critical"})
        return bool(critical), critical


@dataclass(frozen=True)
class NewsItem:
    title: str
    importance: str
    sentiment: float | None = None
    assets: tuple[str, ...] = ()


class NewsImpactAggregator:
    def aggregate(self, items: Sequence[NewsItem]) -> dict[str, float]:
        result: dict[str, list[float]] = {}
        for item in items:
            if item.sentiment is None:
                continue
            for asset in item.assets:
                result.setdefault(asset, []).append(item.sentiment)
        return {asset: sum(values) / len(values) for asset, values in result.items() if values}
