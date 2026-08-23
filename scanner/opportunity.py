from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Opportunity:
    symbol: str
    direction: str
    score: float
    confidence: float
    risk_score: float = 0.0
    data_quality: float = 1.0

    @property
    def rank_score(self) -> float:
        score = max(0.0, min(100.0, self.score))
        confidence = max(0.0, min(1.0, self.confidence))
        risk = max(0.0, min(1.0, self.risk_score))
        quality = max(0.0, min(1.0, self.data_quality))
        return score * confidence * quality * (1.0 - risk)


class OpportunityRanker:
    def rank(self, opportunities: tuple[Opportunity, ...]) -> tuple[Opportunity, ...]:
        return tuple(sorted(opportunities, key=lambda item: item.rank_score, reverse=True))
