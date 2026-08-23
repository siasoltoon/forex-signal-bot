from __future__ import annotations

from collections.abc import Iterable

from decision.contracts import DecisionAction, DecisionEvidence, DecisionResult


class DecisionEngine:
    """Conservative weighted decision engine; disagreement always reduces confidence."""

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
        reasons = tuple(item.reason for item in items if item.reason)
        active_blockers = list(blockers)
        if not items:
            active_blockers.append("no_evidence")

        quality = max(0.0, min(1.0, data_quality))
        totals = {"BUY": 0.0, "SELL": 0.0}
        for item in items:
            direction = item.direction.upper()
            if direction in totals:
                totals[direction] += max(0.0, item.strength) * max(0.0, item.weight) * max(0.0, min(1.0, item.quality))

        directional = totals["BUY"] + totals["SELL"]
        score = (totals["BUY"] - totals["SELL"]) / directional if directional else 0.0
        disagreement = (2.0 * min(totals["BUY"], totals["SELL"]) / directional) if directional else 1.0
        confidence = max(0.0, min(1.0, abs(score) * quality * (1.0 - disagreement)))

        if disagreement > maximum_disagreement:
            active_blockers.append("high_model_disagreement")
        if confidence < minimum_confidence:
            active_blockers.append("low_confidence")
        if quality < minimum_confidence:
            active_blockers.append("poor_data_quality")

        if active_blockers:
            action = DecisionAction.NO_TRADE
        elif score > 0:
            action = DecisionAction.BUY
        elif score < 0:
            action = DecisionAction.SELL
        else:
            action = DecisionAction.WAIT

        return DecisionResult(
            action=action,
            score=score,
            confidence=confidence,
            disagreement=disagreement,
            blockers=tuple(dict.fromkeys(active_blockers)),
            reasons=reasons,
        )


__all__ = ["DecisionEngine"]
