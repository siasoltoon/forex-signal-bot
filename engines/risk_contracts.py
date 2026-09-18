from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskLimits:
    per_trade_pct: float = 1.0
    daily_loss_pct: float = 3.0
    weekly_loss_pct: float = 6.0
    monthly_loss_pct: float = 12.0
    max_open_trades: int = 5
    max_portfolio_exposure_pct: float = 20.0

    def __post_init__(self) -> None:
        if not 0 < self.per_trade_pct <= 100:
            raise ValueError("per_trade_pct must be in (0, 100]")
        if min(self.daily_loss_pct, self.weekly_loss_pct, self.monthly_loss_pct) <= 0:
            raise ValueError("loss limits must be positive")
        if self.max_open_trades < 1:
            raise ValueError("max_open_trades must be positive")


@dataclass(frozen=True)
class PositionSizingRequest:
    account_equity: float
    risk_pct: float
    entry: float
    stop: float
    volatility_factor: float = 1.0


@dataclass(frozen=True)
class PositionSizingResult:
    quantity: float
    cash_risk: float
    stop_distance: float
    blocked: bool = False
    reason: str | None = None


class RiskEngine:
    """Pure risk math; broker execution is intentionally outside this layer."""

    def size(self, request: PositionSizingRequest) -> PositionSizingResult:
        if request.account_equity <= 0 or request.risk_pct <= 0:
            return PositionSizingResult(0.0, 0.0, 0.0, True, "invalid account or risk")
        distance = abs(request.entry - request.stop)
        if distance <= 0:
            return PositionSizingResult(0.0, 0.0, 0.0, True, "invalid stop distance")
        if request.volatility_factor <= 0:
            return PositionSizingResult(0.0, 0.0, distance, True, "invalid volatility factor")
        cash_risk = request.account_equity * request.risk_pct / 100.0
        quantity = cash_risk / (distance * request.volatility_factor)
        return PositionSizingResult(quantity, cash_risk, distance)
