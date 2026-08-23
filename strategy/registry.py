from __future__ import annotations

from threading import RLock
from typing import Iterable

from strategy.contracts import Strategy, StrategyFactory


class StrategyRegistry:
    """Thread-safe registry for strategy factories."""

    def __init__(self) -> None:
        self._factories: dict[str, StrategyFactory] = {}
        self._lock = RLock()

    def register(self, name: str, factory: StrategyFactory, *, replace: bool = False) -> None:
        key = self._normalize(name)
        with self._lock:
            if key in self._factories and not replace:
                raise ValueError(f"Strategy already registered: {key}")
            self._factories[key] = factory

    def unregister(self, name: str) -> None:
        with self._lock:
            self._factories.pop(self._normalize(name), None)

    def create(self, name: str) -> Strategy:
        key = self._normalize(name)
        with self._lock:
            factory = self._factories.get(key)
        if factory is None:
            raise KeyError(f"Unknown strategy: {key}")
        strategy = factory()
        if not hasattr(strategy, "evaluate"):
            raise TypeError(f"Factory for {key} did not return a strategy")
        return strategy

    def names(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._factories))

    def register_many(self, entries: Iterable[tuple[str, StrategyFactory]], *, replace: bool = False) -> None:
        for name, factory in entries:
            self.register(name, factory, replace=replace)

    @staticmethod
    def _normalize(name: str) -> str:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Strategy name must be a non-empty string")
        return name.strip().lower()
