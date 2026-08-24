from __future__ import annotations

from collections import defaultdict
from threading import Lock
from typing import Mapping

from .contracts import MetricSample
import time


class MetricsRegistry:
    def __init__(self) -> None:
        self._values: dict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)
        self._lock = Lock()

    def increment(self, name: str, amount: float = 1.0, labels: Mapping[str, str] | None = None) -> MetricSample:
        key = (name, tuple(sorted((labels or {}).items())))
        with self._lock:
            self._values[key] += amount
            value = self._values[key]
        return MetricSample(name, value, time.time(), dict(key[1]))

    def set(self, name: str, value: float, labels: Mapping[str, str] | None = None) -> MetricSample:
        key = (name, tuple(sorted((labels or {}).items())))
        with self._lock:
            self._values[key] = value
        return MetricSample(name, value, time.time(), dict(key[1]))

    def snapshot(self) -> tuple[MetricSample, ...]:
        now = time.time()
        with self._lock:
            return tuple(MetricSample(name, value, now, dict(labels)) for (name, labels), value in self._values.items())
