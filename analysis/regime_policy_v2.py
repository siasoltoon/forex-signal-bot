from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MarketRegime(StrEnum):
    TREND = "TREND"
    RANGE = "RANGE"
    BREAKOUT = "BREAKOUT"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    ACCUMULATION = "ACCUMULATION"
    DISTRIBUTION = "DISTRIBUTION"
    EXPANSION = "EXPANSION"
    CONTRACTION = "CONTRACTION"
    CRISIS = "CRISIS"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class RegimePolicy:
    regime: MarketRegime
    preferred_styles: tuple[str, ...] = ()
    blocked_styles: tuple[str, ...] = ()
    confidence_multiplier: float = 1.0


class RegimePolicyBook:
    def __init__(self, policies: tuple[RegimePolicy, ...] = ()) -> None:
        self._policies = {policy.regime: policy for policy in policies}

    def set(self, policy: RegimePolicy) -> None:
        if policy.confidence_multiplier < 0:
            raise ValueError("confidence_multiplier cannot be negative")
        self._policies[policy.regime] = policy

    def get(self, regime: MarketRegime) -> RegimePolicy:
        return self._policies.get(regime, RegimePolicy(regime=regime))

    def allowed(self, regime: MarketRegime, styles: tuple[str, ...]) -> tuple[str, ...]:
        policy = self.get(regime)
        blocked = set(policy.blocked_styles)
        return tuple(style for style in styles if style not in blocked)

    def suggestions(self, regime: MarketRegime) -> tuple[str, ...]:
        return self.get(regime).preferred_styles
