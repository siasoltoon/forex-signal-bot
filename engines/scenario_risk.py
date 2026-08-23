from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RiskPlan:
    entry: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    position_size: float
    valid: bool


class ScenarioRiskEngine:
    def build(self, entry: float, stop_loss: float, take_profit: float, account_size: float, risk_fraction: float) -> RiskPlan:
        if account_size <= 0 or risk_fraction <= 0 or risk_fraction > 1:
            raise ValueError("invalid account or risk fraction")
        distance = abs(entry - stop_loss)
        if distance <= 0:
            return RiskPlan(entry, stop_loss, take_profit, 0.0, 0.0, False)
        reward = abs(take_profit - entry)
        rr = reward / distance
        size = account_size * risk_fraction / distance
        return RiskPlan(entry, stop_loss, take_profit, rr, size, rr > 0)

    def approve(self, plan: RiskPlan, min_rr: float = 1.0) -> bool:
        return plan.valid and plan.risk_reward >= min_rr
