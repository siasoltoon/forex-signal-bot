from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TimeframeView:
    timeframe: str
    direction: str
    strength: float = 0.0
    quality: float = 1.0


@dataclass(frozen=True, slots=True)
class MultiTimeframeResult:
    higher: tuple[TimeframeView, ...] = ()
    middle: tuple[TimeframeView, ...] = ()
    lower: tuple[TimeframeView, ...] = ()
    alignment: float = 0.0
    conflict: float = 1.0


class MultiTimeframeEngine:
    def evaluate(
        self,
        *,
        higher: tuple[TimeframeView, ...] = (),
        middle: tuple[TimeframeView, ...] = (),
        lower: tuple[TimeframeView, ...] = (),
    ) -> MultiTimeframeResult:
        views = (*higher, *middle, *lower)
        if not views:
            return MultiTimeframeResult()
        signed = []
        for view in views:
            direction = view.direction.upper()
            sign = 1.0 if direction == "BUY" else -1.0 if direction == "SELL" else 0.0
            signed.append(sign * max(0.0, min(1.0, view.strength)) * max(0.0, min(1.0, view.quality)))
        positive = sum(value for value in signed if value > 0)
        negative = sum(abs(value) for value in signed if value < 0)
        total = positive + negative
        if total == 0:
            return MultiTimeframeResult(higher, middle, lower, 0.0, 1.0)
        alignment = abs(positive - negative) / total
        return MultiTimeframeResult(higher, middle, lower, alignment, 1.0 - alignment)
