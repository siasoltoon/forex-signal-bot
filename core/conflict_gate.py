from __future__ import annotations

from dataclasses import dataclass

from analysis.weighting import Consensus


@dataclass(frozen=True, slots=True)
class ConflictDecision:
    allowed: bool
    confidence_multiplier: float
    reason: str


class ConflictGate:
    def __init__(self, *, maximum_disagreement: float = 0.60, minimum_alignment: float = 0.40) -> None:
        if not 0.0 <= maximum_disagreement <= 1.0:
            raise ValueError("maximum_disagreement must be between 0 and 1")
        if not 0.0 <= minimum_alignment <= 1.0:
            raise ValueError("minimum_alignment must be between 0 and 1")
        self.maximum_disagreement = maximum_disagreement
        self.minimum_alignment = minimum_alignment

    def evaluate(self, consensus: Consensus) -> ConflictDecision:
        if consensus.evidence_count == 0:
            return ConflictDecision(False, 0.0, "no_evidence")
        if consensus.disagreement > self.maximum_disagreement:
            return ConflictDecision(False, 0.0, "high_model_disagreement")
        if consensus.score < self.minimum_alignment:
            return ConflictDecision(False, 0.0, "weak_alignment")
        return ConflictDecision(True, max(0.0, 1.0 - consensus.disagreement), "acceptable_alignment")
