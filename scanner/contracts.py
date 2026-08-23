from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScanRequest:
    market: str
    symbols: tuple[str, ...]
    timeframes: tuple[str, ...]
    styles: tuple[str, ...] = ()
    max_results: int = 20


@dataclass(frozen=True, slots=True)
class Opportunity:
    symbol: str
    timeframe: str
    direction: str
    score: float
    confidence: float
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ScanResult:
    requested: int
    evaluated: int
    opportunities: tuple[Opportunity, ...]


__all__ = ["Opportunity", "ScanRequest", "ScanResult"]
