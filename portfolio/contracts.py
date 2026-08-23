from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Position:
    symbol: str
    side: str
    quantity: float
    entry_price: float
    stop_loss: float | None = None
    take_profit: tuple[float, ...] = ()


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    equity: float
    positions: tuple[Position, ...] = ()
    total_exposure: float = 0.0
    concentration_score: float = 0.0
    correlation_risk: float = 0.0
    stress_loss: float = 0.0


__all__ = ["Position", "PortfolioSnapshot"]
