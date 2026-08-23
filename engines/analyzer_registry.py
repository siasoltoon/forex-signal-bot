from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


Analyzer = Callable[..., Any]


@dataclass(frozen=True, slots=True)
class AnalyzerSpec:
    name: str
    analyzer: Analyzer
    enabled: bool = True
    default_weight: float = 1.0


class AnalyzerRegistry:
    def __init__(self) -> None:
        self._items: dict[str, AnalyzerSpec] = {}

    def register(self, spec: AnalyzerSpec) -> None:
        key = spec.name.strip().lower()
        if not key:
            raise ValueError("analyzer name is required")
        if spec.default_weight < 0:
            raise ValueError("default weight must be non-negative")
        self._items[key] = spec

    def get(self, name: str) -> AnalyzerSpec:
        try:
            return self._items[name.strip().lower()]
        except KeyError as exc:
            raise KeyError(f"unknown analyzer: {name}") from exc

    def active(self) -> tuple[AnalyzerSpec, ...]:
        return tuple(item for item in self._items.values() if item.enabled)

    def names(self) -> tuple[str, ...]:
        return tuple(self._items)
