from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RiskGateResult:
    blocked: bool
    risk_per_trade: float
    exposure: float
    reasons: tuple[str, ...]


class RiskGateEngine:
    def evaluate(
        self,
        risk_per_trade: float,
        exposure: float,
        max_risk_per_trade: float = 0.02,
        max_exposure: float = 0.10,
        emergency_stop: bool = False,
    ) -> RiskGateResult:
        reasons: list[str] = []
        if risk_per_trade < 0:
            reasons.append("negative risk")
        elif risk_per_trade > max_risk_per_trade:
            reasons.append("risk per trade limit")
        if exposure < 0:
            reasons.append("negative exposure")
        elif exposure > max_exposure:
            reasons.append("portfolio exposure limit")
        if emergency_stop:
            reasons.append("emergency stop")
        return RiskGateResult(bool(reasons), risk_per_trade, exposure, tuple(reasons))
