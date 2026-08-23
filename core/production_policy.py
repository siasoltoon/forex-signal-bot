"""Production safety policy used by live orchestration boundaries."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DecisionMode(str, Enum):
    LIVE = "live"
    PAPER = "paper"
    RESEARCH = "research"


@dataclass(frozen=True)
class ProductionPolicy:
    mode: DecisionMode = DecisionMode.PAPER
    allow_order_submission: bool = False
    require_fresh_market_data: bool = True
    require_valid_risk: bool = True
    require_scenario: bool = True
    require_stop_loss: bool = True
    max_signal_age_seconds: int = 60

    def can_submit(self, runtime_ready: bool, market_fresh: bool, risk_valid: bool,
                   scenario_valid: bool, stop_loss_valid: bool, signal_age_seconds: int) -> bool:
        """Return whether live order submission is allowed by every safety gate.

        Positional and keyword arguments are both accepted for compatibility;
        the safety checks remain fail-closed.
        """
        if self.mode is not DecisionMode.LIVE or not self.allow_order_submission:
            return False
        if not runtime_ready:
            return False
        if self.require_fresh_market_data and not market_fresh:
            return False
        if self.require_valid_risk and not risk_valid:
            return False
        if self.require_scenario and not scenario_valid:
            return False
        if self.require_stop_loss and not stop_loss_valid:
            return False
        return signal_age_seconds <= self.max_signal_age_seconds

    def validate(self) -> None:
        if self.max_signal_age_seconds <= 0:
            raise ValueError("max_signal_age_seconds must be positive")
        if self.mode is DecisionMode.LIVE and not self.allow_order_submission:
            raise ValueError("LIVE mode requires explicit allow_order_submission=True")
