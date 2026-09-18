from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RiskLimits:
    max_risk_percent: float = 1.0
    max_position_percent: float = 25.0
    max_daily_loss_percent: float = 3.0
    max_total_exposure_percent: float = 100.0


@dataclass(frozen=True, slots=True)
class RiskRequest:
    equity: float
    entry: float
    stop: float
    risk_percent: float
    volatility_multiplier: float = 1.0
    liquidity_multiplier: float = 1.0
    existing_exposure_percent: float = 0.0
    daily_loss_percent: float = 0.0


@dataclass(frozen=True, slots=True)
class RiskResult:
    allowed: bool
    position_size: float
    risk_amount: float
    effective_risk_percent: float
    reason: str


class RiskEngine:
    def __init__(self, limits: RiskLimits | None = None) -> None:
        self.limits = limits or RiskLimits()

    def calculate(self, request: RiskRequest) -> RiskResult:
        if request.equity <= 0:
            return RiskResult(False, 0.0, 0.0, 0.0, "invalid_equity")
        if request.entry <= 0 or request.stop <= 0 or request.entry == request.stop:
            return RiskResult(False, 0.0, 0.0, 0.0, "invalid_stop_distance")
        if request.risk_percent <= 0 or request.risk_percent > self.limits.max_risk_percent:
            return RiskResult(False, 0.0, 0.0, 0.0, "risk_limit_exceeded")
        if request.daily_loss_percent >= self.limits.max_daily_loss_percent:
            return RiskResult(False, 0.0, 0.0, 0.0, "daily_loss_limit")
        if request.existing_exposure_percent >= self.limits.max_total_exposure_percent:
            return RiskResult(False, 0.0, 0.0, 0.0, "exposure_limit")
        if request.volatility_multiplier <= 0 or request.liquidity_multiplier <= 0:
            return RiskResult(False, 0.0, 0.0, 0.0, "invalid_adjustment")
        effective = request.risk_percent * request.volatility_multiplier * request.liquidity_multiplier
        effective = min(effective, self.limits.max_risk_percent)
        risk_amount = request.equity * effective / 100
        stop_distance = abs(request.entry - request.stop)
        size = risk_amount / stop_distance
        max_size = request.equity * self.limits.max_position_percent / 100 / request.entry
        size = min(size, max_size)
        return RiskResult(True, size, size * stop_distance, effective, "approved")
