from __future__ import annotations

from collections.abc import Iterable

from core.decision import DecisionAction, DecisionEvidence, DecisionResult


class DecisionEngine:
    """Deterministic evidence aggregator with explicit NO_TRADE gates."""

    def evaluate(
        self,
        evidence: Iterable[DecisionEvidence],
        *,
        data_quality: float = 1.0,
        minimum_confidence: float = 0.60,
        maximum_disagreement: float = 0.55,
        blockers: Iterable[str] = (),
    ) -> DecisionResult:
        items = tuple(evidence)
        normalized_blockers = list(blockers)
        if not items:
            normalized_blockers.append("no_evidence")

        quality = max(0.0, min(1.0, float(data_quality)))
        weighted = {"BUY": 0.0, "SELL": 0.0, "NEUTRAL": 0.0}
        total_weight = 0.0
        for item in items:
            direction = item.direction.upper()
            if direction not in weighted:
                continue
            contribution = max(0.0, min(1.0, item.strength)) * max(0.0, item.weight) * max(0.0, min(1.0, item.quality))
            weighted[direction] += contribution
            total_weight += max(0.0, item.weight)

        if total_weight <= 0:
            normalized_blockers.append("zero_effective_weight")
            score = 0.0
            action = DecisionAction.NO_TRADE
            disagreement = 1.0
        else:
            buy = weighted["BUY"]
            sell = weighted["SELL"]
            directional = buy + sell
            score = (buy - sell) / directional if directional else 0.0
            action = DecisionAction.BUY if score > 0 else DecisionAction.SELL if score < 0 else DecisionAction.WAIT
            disagreement = min(1.0, (2.0 * min(buy, sell) / directional) if directional else 1.0)

        confidence = max(0.0, min(1.0, abs(score) * quality * (1.0 - disagreement)))
        if disagreement > maximum_disagreement:
            normalized_blockers.append("high_model_disagreement")
        if confidence < minimum_confidence:
            normalized_blockers.append("low_confidence")
        if quality < minimum_confidence:
            normalized_blockers.append("poor_data_quality")

        if normalized_blockers:
            action = DecisionAction.NO_TRADE

        reasons = tuple(item.reason for item in items if item.reason)
        return DecisionResult(
            action=action,
            confidence=confidence,
            score=score,
            disagreement=disagreement,
            reasons=reasons,
            blockers=tuple(dict.fromkeys(normalized_blockers)),
            evidence=items,
        )


__all__ = ["DecisionEngine"]
