from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RiskLimits:
    per_trade_percent: float = 1.0
    daily_loss_percent: float = 3.0
    weekly_loss_percent: float = 6.0
    monthly_loss_percent: float = 10.0
    max_open_trades: int = 5
    max_portfolio_exposure_percent: float = 20.0


@dataclass(frozen=True, slots=True)
class PositionSizingInput:
    account_size: float
    risk_percent: float
    entry: float
    stop_loss: float
    volatility_factor: float = 1.0
    liquidity_factor: float = 1.0
    exposure_factor: float = 1.0


@dataclass(frozen=True, slots=True)
class RiskDecision:
    allowed: bool
    risk_percent: float
    position_size: float
    reasons: tuple[str, ...] = ()


__all__ = ["PositionSizingInput", "RiskDecision", "RiskLimits"]
