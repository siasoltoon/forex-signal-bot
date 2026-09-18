from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping


class WeightMode(StrEnum):
    STATIC = "STATIC"
    DYNAMIC = "DYNAMIC"
    REGIME_BASED = "REGIME_BASED"
    PERFORMANCE_BASED = "PERFORMANCE_BASED"


@dataclass(frozen=True, slots=True)
class WeightProfile:
    mode: WeightMode
    values: Mapping[str, float]
    default: float = 1.0

    def resolve(self, name: str, *, regime: str | None = None, performance: float | None = None) -> float:
        base = max(0.0, self.values.get(name.strip().lower(), self.default))
        if self.mode is WeightMode.PERFORMANCE_BASED and performance is not None:
            return base * max(0.0, min(2.0, performance))
        if self.mode is WeightMode.REGIME_BASED and regime:
            key = f"{regime.strip().lower()}:{name.strip().lower()}"
            return max(0.0, self.values.get(key, base))
        return base
