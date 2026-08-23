from __future__ import annotations

from typing import Iterable

from decision.contracts import AnalysisEvidence, DecisionAction, DecisionPolicy, DecisionResult


class DecisionEngine:
    """Combines normalized evidence without using majority vote alone."""

    def __init__(self, policy: DecisionPolicy | None = None) -> None:
        self.policy = policy or DecisionPolicy()

    def decide(self, evidence: Iterable[AnalysisEvidence], *, data_quality: float = 1.0, regime_known: bool = True) -> DecisionResult:
        items = tuple(evidence)
        if not items:
            return DecisionResult(DecisionAction.NO_TRADE, 0.0, 0.0, 1.0, reasons=("no_evidence",))
        if self.policy.no_trade_on_missing_data and data_quality < self.policy.minimum_quality:
            return DecisionResult(DecisionAction.NO_TRADE, 0.0, data_quality, 1.0, reasons=("insufficient_data_quality",), evidence=items)
        if not regime_known:
            return DecisionResult(DecisionAction.NO_TRADE, 0.0, 0.0, 1.0, reasons=("unknown_market_regime",), evidence=items)

        total_weight = sum(max(0.0, e.weight) for e in items) or 1.0
        score = sum(e.contribution for e in items) / total_weight
        positive = sum(max(0.0, e.contribution) for e in items)
        negative = sum(max(0.0, -e.contribution) for e in items)
        magnitude = positive + negative
        disagreement = 0.0 if magnitude == 0 else min(1.0, 2.0 * min(positive, negative) / magnitude)
        confidence = max(0.0, min(1.0, abs(score) * data_quality * (1.0 - disagreement)))

        if disagreement > self.policy.maximum_disagreement or confidence < self.policy.minimum_confidence:
            action = DecisionAction.NO_TRADE
            reason = "high_model_disagreement" if disagreement > self.policy.maximum_disagreement else "low_confidence"
        elif score > 0:
            action, reason = DecisionAction.BUY, "weighted_evidence_bullish"
        elif score < 0:
            action, reason = DecisionAction.SELL, "weighted_evidence_bearish"
        else:
            action, reason = DecisionAction.WAIT, "neutral_evidence"

        return DecisionResult(action, score, confidence, disagreement, reasons=(reason,), evidence=items)
