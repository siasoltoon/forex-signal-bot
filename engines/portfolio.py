from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PositionExposure:
    symbol: str
    notional: float
    risk_amount: float


@dataclass(frozen=True, slots=True)
class PortfolioRisk:
    total_notional: float
    total_risk: float
    concentration: float
    allowed: bool
    reason: str


class PortfolioRiskEngine:
    def evaluate(self, positions: tuple[PositionExposure, ...], equity: float, max_risk_percent: float = 5.0, max_concentration: float = 0.40) -> PortfolioRisk:
        if equity <= 0:
            return PortfolioRisk(0.0, 0.0, 1.0, False, "invalid_equity")
        total_notional = sum(abs(item.notional) for item in positions)
        total_risk = sum(max(0.0, item.risk_amount) for item in positions)
        concentration = max((abs(item.notional) / total_notional for item in positions), default=0.0)
        allowed = total_risk <= equity * max_risk_percent / 100 and concentration <= max_concentration
        reason = "approved" if allowed else "portfolio_limit"
        return PortfolioRisk(total_notional, total_risk, concentration, allowed, reason)
