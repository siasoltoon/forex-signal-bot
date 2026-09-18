from __future__ import annotations

from dataclasses import dataclass

from risk.portfolio_guard import PortfolioRiskResult


@dataclass(frozen=True, slots=True)
class RiskDecision:
    allowed: bool
    decision: str
    reason: str | None = None


class RiskDecisionGate:
    def evaluate(self, *, requested_decision: str, portfolio: PortfolioRiskResult) -> RiskDecision:
        decision = requested_decision.upper()
        if decision not in {"BUY", "SELL", "WAIT", "NO_TRADE"}:
            return RiskDecision(False, "NO_TRADE", "invalid_decision")
        if decision == "NO_TRADE":
            return RiskDecision(False, "NO_TRADE", "decision_engine_no_trade")
        if not portfolio.allowed:
            return RiskDecision(False, "NO_TRADE", portfolio.reason or "portfolio_risk")
        return RiskDecision(True, decision)
