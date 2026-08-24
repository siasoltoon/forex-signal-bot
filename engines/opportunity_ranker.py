from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class Opportunity:
    symbol: str
    score: float
    confidence: float
    risk: float
    decision: str


class OpportunityRanker:
    def rank(self, opportunities: Sequence[Opportunity]) -> tuple[Opportunity, ...]:
        return tuple(sorted(opportunities, key=lambda x: (x.score, x.confidence, -x.risk), reverse=True))

    def top(self, opportunities: Sequence[Opportunity], limit: int = 10) -> tuple[Opportunity, ...]:
        if limit <= 0:
            return ()
        return self.rank(opportunities)[:limit]
