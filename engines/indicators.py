from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from .market_data import Candle


@dataclass(frozen=True, slots=True)
class IndicatorSnapshot:
    sma_fast: float | None
    sma_slow: float | None
    ema_fast: float | None
    ema_slow: float | None
    rsi: float | None
    atr: float | None
    volatility: float | None


class IndicatorEngine:
    @staticmethod
    def _sma(values: list[float], period: int) -> float | None:
        return sum(values[-period:]) / period if len(values) >= period else None

    @staticmethod
    def _ema(values: list[float], period: int) -> float | None:
        if len(values) < period:
            return None
        result = sum(values[:period]) / period
        alpha = 2 / (period + 1)
        for value in values[period:]:
            result = alpha * value + (1 - alpha) * result
        return result

    @staticmethod
    def _rsi(values: list[float], period: int = 14) -> float | None:
        if len(values) <= period:
            return None
        gains: list[float] = []
        losses: list[float] = []
        for before, after in zip(values, values[1:]):
            change = after - before
            gains.append(max(change, 0.0))
            losses.append(max(-change, 0.0))
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        for gain, loss in zip(gains[period:], losses[period:]):
            avg_gain = ((avg_gain * (period - 1)) + gain) / period
            avg_loss = ((avg_loss * (period - 1)) + loss) / period
        if avg_loss == 0:
            return 100.0
        return 100 - (100 / (1 + avg_gain / avg_loss))

    @staticmethod
    def _atr(candles: list[Candle], period: int = 14) -> float | None:
        if len(candles) <= period:
            return None
        true_ranges: list[float] = []
        previous_close: float | None = None
        for candle in candles:
            if previous_close is None:
                tr = candle.high - candle.low
            else:
                tr = max(candle.high - candle.low, abs(candle.high - previous_close), abs(candle.low - previous_close))
            true_ranges.append(tr)
            previous_close = candle.close
        return sum(true_ranges[-period:]) / period

    @staticmethod
    def _volatility(values: list[float], period: int = 20) -> float | None:
        if len(values) < period + 1:
            return None
        returns = [values[i] / values[i - 1] - 1 for i in range(len(values) - period, len(values))]
        mean = sum(returns) / len(returns)
        return sqrt(sum((value - mean) ** 2 for value in returns) / len(returns))

    def compute(self, candles: tuple[Candle, ...], fast: int = 20, slow: int = 50) -> IndicatorSnapshot:
        closes = [c.close for c in candles]
        return IndicatorSnapshot(
            sma_fast=self._sma(closes, fast),
            sma_slow=self._sma(closes, slow),
            ema_fast=self._ema(closes, fast),
            ema_slow=self._ema(closes, slow),
            rsi=self._rsi(closes),
            atr=self._atr(list(candles)),
            volatility=self._volatility(closes),
        )
