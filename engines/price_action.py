from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .market_data import Candle


class Direction(StrEnum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


@dataclass(frozen=True, slots=True)
class PriceActionSnapshot:
    direction: Direction
    strength: float
    higher_high: bool
    lower_low: bool
    breakout: bool
    rejection: bool
    support: float | None
    resistance: float | None


class PriceActionEngine:
    def analyze(self, candles: tuple[Candle, ...], lookback: int = 20) -> PriceActionSnapshot:
        if len(candles) < max(3, lookback):
            return PriceActionSnapshot(Direction.NEUTRAL, 0.0, False, False, False, False, None, None)
        window = candles[-lookback:]
        previous = candles[-2]
        current = candles[-1]
        highs = [c.high for c in window[:-1]]
        lows = [c.low for c in window[:-1]]
        resistance = max(highs)
        support = min(lows)
        higher_high = current.high > max(highs[-max(2, lookback // 3):])
        lower_low = current.low < min(lows[-max(2, lookback // 3):])
        breakout = current.close > resistance or current.close < support
        candle_range = max(current.high - current.low, 1e-12)
        body = abs(current.close - current.open)
        rejection = body / candle_range < 0.35 and (current.high > previous.high or current.low < previous.low)
        if current.close > previous.close and higher_high:
            direction = Direction.BULLISH
        elif current.close < previous.close and lower_low:
            direction = Direction.BEARISH
        else:
            direction = Direction.NEUTRAL
        strength = min(1.0, body / candle_range)
        if breakout:
            strength = min(1.0, strength + 0.25)
        return PriceActionSnapshot(direction, strength, higher_high, lower_low, breakout, rejection, support, resistance)
