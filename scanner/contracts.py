from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScanCandidate:
    symbol: str
    timeframe: str
    available: bool = True


@dataclass(frozen=True, slots=True)
class ScanResult:
    scanned: int
    eligible: int
    opportunities: int
    high_quality: int
    rejected: int
