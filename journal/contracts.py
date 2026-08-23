from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class JournalEntry:
    entry_id: str
    symbol: str
    side: str
    setup: str
    entry: float
    risk: float
    market_regime: str
    reason: str
    exit: float | None = None
    result: float | None = None
    mistakes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CoachInsight:
    category: str
    observation: str
    evidence_count: int
    confidence: float


__all__ = ["CoachInsight", "JournalEntry"]
