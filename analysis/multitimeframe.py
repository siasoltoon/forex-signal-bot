from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TimeframeRole(StrEnum):
    CONTEXT = "CONTEXT"
    STRUCTURE = "STRUCTURE"
    ENTRY = "ENTRY"


@dataclass(frozen=True, slots=True)
class TimeframeEvidence:
    timeframe: str
    role: TimeframeRole
    direction: str
    confidence: float


@dataclass(frozen=True, slots=True)
class TimeframeAlignment:
    aligned: bool
    conflict_score: float
    evidence: tuple[TimeframeEvidence, ...]


class MultiTimeframeEngine:
    def evaluate(self, evidence: tuple[TimeframeEvidence, ...]) -> TimeframeAlignment:
        if not evidence:
            return TimeframeAlignment(False, 1.0, ())
        valid = tuple(item for item in evidence if 0 <= item.confidence <= 1)
        if not valid:
            return TimeframeAlignment(False, 1.0, valid)
        directional = [item.direction for item in valid if item.direction in {"BULLISH", "BEARISH"}]
        if not directional:
            return TimeframeAlignment(False, 1.0, valid)
        conflicts = sum(direction != directional[0] for direction in directional)
        score = conflicts / len(directional)
        return TimeframeAlignment(score == 0, score, valid)
