from __future__ import annotations

from statistics import mean, pstdev
from typing import Sequence

from .analysis_runtime import AnalysisEvidence
from .data_runtime import MarketSnapshot


def _closes(snapshot: MarketSnapshot) -> list[float]:
    return [c.close for c in snapshot.candles]


class MomentumAnalyzer:
    name = "momentum"
    supported_timeframes = {"1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"}

    async def analyze(self, snapshot: MarketSnapshot) -> AnalysisEvidence:
        closes = _closes(snapshot)
        if len(closes) < 3:
            return AnalysisEvidence(self.name, "NEUTRAL", 0, 0, snapshot.quality.score, snapshot.request.timeframe, {"reason": "insufficient_data"})
        change = (closes[-1] - closes[-3]) / closes[-3] if closes[-3] else 0.0
        direction = "BUY" if change > 0 else "SELL" if change < 0 else "NEUTRAL"
        strength = min(100.0, abs(change) * 10_000)
        return AnalysisEvidence(self.name, direction, strength, min(100.0, 50 + strength / 2), snapshot.quality.score, snapshot.request.timeframe, {"return_2": change})


class TrendAnalyzer:
    name = "trend"
    supported_timeframes = {"5m", "15m", "30m", "1h", "4h", "1d", "1w"}

    async def analyze(self, snapshot: MarketSnapshot) -> AnalysisEvidence:
        closes = _closes(snapshot)
        if len(closes) < 20:
            return AnalysisEvidence(self.name, "NEUTRAL", 0, 0, snapshot.quality.score, snapshot.request.timeframe, {"reason": "insufficient_data"})
        fast = mean(closes[-10:])
        slow = mean(closes[-20:])
        direction = "BUY" if fast > slow else "SELL" if fast < slow else "NEUTRAL"
        strength = min(100.0, abs(fast - slow) / max(abs(slow), 1e-12) * 10_000)
        return AnalysisEvidence(self.name, direction, strength, min(100.0, 55 + strength / 2), snapshot.quality.score, snapshot.request.timeframe, {"fast_mean": fast, "slow_mean": slow})


class VolatilityAnalyzer:
    name = "volatility"
    supported_timeframes = {"5m", "15m", "1h", "4h", "1d"}

    async def analyze(self, snapshot: MarketSnapshot) -> AnalysisEvidence:
        closes = _closes(snapshot)
        returns = [(b - a) / a for a, b in zip(closes[-21:-1], closes[-20:]) if a]
        vol = pstdev(returns) if len(returns) > 1 else 0.0
        direction = "NEUTRAL"
        return AnalysisEvidence(self.name, direction, min(100.0, vol * 10_000), min(100.0, snapshot.quality.score), snapshot.quality.score, snapshot.request.timeframe, {"realized_volatility": vol})


def default_real_analyzers() -> tuple[object, ...]:
    return (MomentumAnalyzer(), TrendAnalyzer(), VolatilityAnalyzer())
