from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TimeframeView:
    timeframe: str
    direction: str
    strength: float
    regime: str | None = None


@dataclass(frozen=True, slots=True)
class MultiTimeframeContext:
    higher: tuple[TimeframeView, ...] = ()
    middle: tuple[TimeframeView, ...] = ()
    lower: tuple[TimeframeView, ...] = ()

    @property
    def views(self) -> tuple[TimeframeView, ...]:
        return self.higher + self.middle + self.lower

    def disagreement(self) -> float:
        directions = [v.direction.lower() for v in self.views if v.direction.lower() in {"bullish", "bearish"}]
        if not directions:
            return 1.0
        bullish = directions.count("bullish")
        bearish = directions.count("bearish")
        return min(bullish, bearish) / max(1, len(directions))


__all__ = ["TimeframeView", "MultiTimeframeContext"]
