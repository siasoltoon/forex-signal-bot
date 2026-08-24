from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
from .contracts import Candle
@dataclass(frozen=True, slots=True)
class QualityReport:
    score: float
    valid: bool
    gaps: int
    duplicates: int
    anomalies: int
    stale: bool
class DataQualityPipeline:
    def validate(self, candles: Sequence[Candle], expected_interval: int|None=None, latest: int|None=None) -> QualityReport:
        gaps=duplicates=anomalies=0; prev=None
        for c in candles:
            if c.high < max(c.open,c.close) or c.low > min(c.open,c.close) or c.low > c.high: anomalies += 1
            if prev is not None:
                if c.timestamp == prev: duplicates += 1
                elif expected_interval and c.timestamp-prev > expected_interval: gaps += 1
            prev=c.timestamp
        stale=bool(latest is not None and candles and candles[-1].timestamp < latest)
        score=max(0.0,1.0-0.25*(gaps+duplicates+anomalies+(1 if stale else 0)))
        return QualityReport(score,bool(candles) and score>0.75,gaps,duplicates,anomalies,stale)
