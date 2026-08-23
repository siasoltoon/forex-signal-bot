from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class PortfolioPosition:
    symbol: str
    market: str
    notional: float
    risk: float
    direction: str


@dataclass(frozen=True)
class PortfolioSnapshot:
    equity: float
    positions: Sequence[PortfolioPosition]

    @property
    def total_exposure(self) -> float:
        return sum(abs(position.notional) for position in self.positions)

    @property
    def total_risk(self) -> float:
        return sum(max(position.risk, 0.0) for position in self.positions)


@dataclass(frozen=True)
class PortfolioRiskResult:
    exposure_pct: float
    risk_pct: float
    concentration_pct: float
    blocked: bool
    reasons: Sequence[str] = ()


class PortfolioRiskEngine:
    def evaluate(self, snapshot: PortfolioSnapshot, max_exposure_pct: float, max_risk_pct: float) -> PortfolioRiskResult:
        if snapshot.equity <= 0:
            return PortfolioRiskResult(0.0, 0.0, 0.0, True, ("invalid equity",))
        exposure_pct = snapshot.total_exposure / snapshot.equity * 100
        risk_pct = snapshot.total_risk / snapshot.equity * 100
        largest = max((abs(p.notional) for p in snapshot.positions), default=0.0)
        concentration = largest / snapshot.total_exposure * 100 if snapshot.total_exposure else 0.0
        reasons = []
        if exposure_pct > max_exposure_pct:
            reasons.append("portfolio exposure limit")
        if risk_pct > max_risk_pct:
            reasons.append("portfolio risk limit")
        return PortfolioRiskResult(exposure_pct, risk_pct, concentration, bool(reasons), tuple(reasons))
