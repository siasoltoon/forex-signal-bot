from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StrategyCandidate:
    name: str
    score: float
    regime: str | None = None
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class StrategySelection:
    selected: tuple[str, ...]
    rejected: tuple[str, ...]


class StrategySelector:
    def select(
        self,
        candidates: tuple[StrategyCandidate, ...],
        *,
        regime: str | None = None,
        limit: int = 3,
    ) -> StrategySelection:
        if limit < 1:
            raise ValueError("limit must be >= 1")
        eligible = [
            item for item in candidates
            if item.enabled and (item.regime is None or regime is None or item.regime == regime)
        ]
        eligible.sort(key=lambda item: item.score, reverse=True)
        selected = tuple(item.name for item in eligible[:limit])
        selected_set = set(selected)
        rejected = tuple(item.name for item in candidates if item.name not in selected_set)
        return StrategySelection(selected, rejected)
