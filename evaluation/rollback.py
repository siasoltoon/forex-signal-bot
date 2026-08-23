from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RollbackDecision:
    rollback: bool
    target_model: str
    reason: str


class RollbackGuard:
    def evaluate(self, *, active_model: str, last_known_good: str, healthy: bool) -> RollbackDecision:
        if healthy:
            return RollbackDecision(False, active_model, "active_model_healthy")
        if not last_known_good:
            return RollbackDecision(False, active_model, "no_known_good_model")
        return RollbackDecision(True, last_known_good, "active_model_unhealthy")
