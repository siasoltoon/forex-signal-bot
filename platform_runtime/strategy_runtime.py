from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .data_runtime import Candle
from .research_engine import Order


@dataclass(frozen=True)
class StrategyDNA:
    name: str
    market: str
    timeframes: tuple[str, ...]
    regime: str
    entry_conditions: tuple[str, ...]
    exit_conditions: tuple[str, ...]
    failure_conditions: tuple[str, ...]


class MovingAverageCrossStrategy:
    name = "moving_average_cross"

    def __init__(self, fast: int = 10, slow: int = 30, quantity: float = 1.0) -> None:
        if fast <= 1 or slow <= fast:
            raise ValueError("slow must be greater than fast > 1")
        self.fast, self.slow, self.quantity = fast, slow, quantity

    def on_candle(self, candles: Sequence[Candle], cash: float) -> Order | None:
        if len(candles) < self.slow + 1:
            return None
        closes = [c.close for c in candles]
        previous_fast = sum(closes[-self.fast-1:-1]) / self.fast
        previous_slow = sum(closes[-self.slow-1:-1]) / self.slow
        current_fast = sum(closes[-self.fast:]) / self.fast
        current_slow = sum(closes[-self.slow:]) / self.slow
        price = closes[-1]
        if previous_fast <= previous_slow and current_fast > current_slow:
            return Order("BUY", self.quantity, price)
        if previous_fast >= previous_slow and current_fast < current_slow:
            return Order("SELL", self.quantity, price)
        return None

    @property
    def dna(self) -> StrategyDNA:
        return StrategyDNA(self.name, "asset_agnostic", (), "trend", ("fast_ma_crosses_slow_ma",), ("opposite_cross",), ("insufficient_data",))
