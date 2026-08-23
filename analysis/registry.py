from __future__ import annotations

from threading import RLock
from typing import Iterable

from analysis.contracts import Analyzer, AnalyzerFactory


class AnalyzerRegistry:
    """Thread-safe registry for analyzer factories."""

    def __init__(self) -> None:
        self._factories: dict[str, AnalyzerFactory] = {}
        self._lock = RLock()

    def register(self, name: str, factory: AnalyzerFactory, *, replace: bool = False) -> None:
        key = self._normalize(name)
        with self._lock:
            if key in self._factories and not replace:
                raise ValueError(f"Analyzer already registered: {key}")
            self._factories[key] = factory

    def unregister(self, name: str) -> None:
        with self._lock:
            self._factories.pop(self._normalize(name), None)

    def create(self, name: str) -> Analyzer:
        key = self._normalize(name)
        with self._lock:
            factory = self._factories.get(key)
        if factory is None:
            raise KeyError(f"Unknown analyzer: {key}")
        analyzer = factory()
        if not hasattr(analyzer, "analyze"):
            raise TypeError(f"Factory for {key} did not return an analyzer")
        return analyzer

    def names(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._factories))

    def __contains__(self, name: str) -> bool:
        with self._lock:
            return self._normalize(name) in self._factories

    @staticmethod
    def _normalize(name: str) -> str:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Analyzer name must be a non-empty string")
        return name.strip().lower()

    def register_many(self, entries: Iterable[tuple[str, AnalyzerFactory]], *, replace: bool = False) -> None:
        for name, factory in entries:
            self.register(name, factory, replace=replace)
