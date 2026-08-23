from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Sequence


@dataclass(frozen=True)
class RiskLimits:
    risk_percent: float = 1.0
    max_position_percent: float = 10.0
    max_portfolio_risk_percent: float = 5.0
    max_drawdown_percent: float = 20.0


@dataclass(frozen=True)
class PositionPlan:
    quantity: float
    risk_amount: float
    stop_distance: float
    blocked: bool
    reasons: tuple[str, ...] = ()


class RiskEngine:
    def __init__(self, limits: RiskLimits | None = None) -> None:
        self.limits = limits or RiskLimits()

    def position_size(self, account_size: float, entry: float, stop: float, volatility_factor: float = 1.0) -> PositionPlan:
        if account_size <= 0 or entry <= 0 or stop <= 0:
            return PositionPlan(0.0, 0.0, 0.0, True, ("invalid_account_or_price",))
        distance = abs(entry - stop)
        if distance == 0 or not isfinite(distance):
            return PositionPlan(0.0, 0.0, distance, True, ("invalid_stop_distance",))
        risk_amount = account_size * self.limits.risk_percent / 100.0
        quantity = risk_amount / distance / max(volatility_factor, 0.01)
        if quantity * entry > account_size * self.limits.max_position_percent / 100.0:
            quantity = account_size * self.limits.max_position_percent / 100.0 / entry
        return PositionPlan(quantity, quantity * distance, distance, False)


@dataclass(frozen=True)
class PositionExposure:
    symbol: str
    market_value: float
    risk_value: float
    correlation_group: str | None = None


@dataclass(frozen=True)
class PortfolioRisk:
    total_value: float
    total_risk: float
    concentration: float
    blocked: bool
    reasons: tuple[str, ...] = ()


class PortfolioRiskEngine:
    def assess(self, account_size: float, positions: Sequence[PositionExposure], limits: RiskLimits | None = None) -> PortfolioRisk:
        limits = limits or RiskLimits()
        total_value = sum(max(0.0, p.market_value) for p in positions)
        total_risk = sum(max(0.0, p.risk_value) for p in positions)
        concentration = max((p.market_value / total_value for p in positions), default=0.0) * 100.0
        reasons: list[str] = []
        if account_size <= 0:
            reasons.append("invalid_account_size")
        if account_size and total_risk / account_size * 100.0 > limits.max_portfolio_risk_percent:
            reasons.append("portfolio_risk_limit")
        if concentration > limits.max_position_percent:
            reasons.append("concentration_limit")
        return PortfolioRisk(total_value, total_risk, concentration, bool(reasons), tuple(reasons))
