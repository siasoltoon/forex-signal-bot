from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RiskPolicy:
    max_risk_percent: float = 1.0
    max_portfolio_exposure_percent: float = 10.0
    minimum_risk_reward: float = 1.5
    max_open_trades: int = 5
    emergency_stop: bool = False
    capital_preservation: bool = False

    def validate(self) -> None:
        if not 0.0 < self.max_risk_percent <= 100.0:
            raise ValueError("max_risk_percent must be between 0 and 100")
        if not 0.0 < self.max_portfolio_exposure_percent <= 100.0:
            raise ValueError("max_portfolio_exposure_percent must be between 0 and 100")
        if self.minimum_risk_reward <= 0:
            raise ValueError("minimum_risk_reward must be positive")
        if self.max_open_trades < 0:
            raise ValueError("max_open_trades cannot be negative")


@dataclass(frozen=True, slots=True)
class RiskDecision:
    allowed: bool
    risk_percent: float
    blockers: tuple[str, ...] = ()


class RiskGate:
    def __init__(self, policy: RiskPolicy) -> None:
        policy.validate()
        self.policy = policy

    def evaluate(self, *, requested_risk_percent: float, open_trades: int, exposure_percent: float) -> RiskDecision:
        blockers: list[str] = []
        requested = max(0.0, requested_risk_percent)
        risk = min(requested, self.policy.max_risk_percent)
        if self.policy.emergency_stop:
            blockers.append("emergency_stop")
        if self.policy.capital_preservation:
            blockers.append("capital_preservation")
        if open_trades >= self.policy.max_open_trades:
            blockers.append("max_open_trades")
        if exposure_percent + risk > self.policy.max_portfolio_exposure_percent:
            blockers.append("max_portfolio_exposure")
        return RiskDecision(not blockers, risk, tuple(blockers))


__all__ = ["RiskDecision", "RiskGate", "RiskPolicy"]
