from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PositionRisk:
    symbol: str
    risk_amount: float
    exposure: float
    direction: str


@dataclass(frozen=True, slots=True)
class PortfolioRiskResult:
    allowed: bool
    total_risk: float
    total_exposure: float
    reason: str | None = None


class PortfolioRiskGuard:
    """Pure portfolio-level safety checks over supplied position risk."""

    def __init__(self, *, max_total_risk: float = 0.05, max_exposure: float = 1.0, max_open_positions: int = 10) -> None:
        if max_total_risk < 0 or max_exposure < 0 or max_open_positions < 0:
            raise ValueError("portfolio limits must be non-negative")
        self.max_total_risk = max_total_risk
        self.max_exposure = max_exposure
        self.max_open_positions = max_open_positions

    def evaluate(self, positions: tuple[PositionRisk, ...]) -> PortfolioRiskResult:
        total_risk = sum(max(0.0, p.risk_amount) for p in positions)
        total_exposure = sum(max(0.0, p.exposure) for p in positions)
        if len(positions) > self.max_open_positions:
            return PortfolioRiskResult(False, total_risk, total_exposure, "maximum_open_positions")
        if total_risk > self.max_total_risk:
            return PortfolioRiskResult(False, total_risk, total_exposure, "maximum_portfolio_risk")
        if total_exposure > self.max_exposure:
            return PortfolioRiskResult(False, total_risk, total_exposure, "maximum_exposure")
        return PortfolioRiskResult(True, total_risk, total_exposure)
