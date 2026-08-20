from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from analysis.confluence.engine import ConfluenceResult
from analysis.market_regime.detector import MarketRegime
from risk.manager import RiskResult


@dataclass(frozen=True)
class SignalDecision:
    """
    Final analytical decision.

    This object does NOT execute trades.
    """

    direction: str
    strength: float
    confidence: float
    regime: str
    risk_reward_ratio: float
    acceptable_risk: bool
    approved: bool
    reasons: list[str]
    metadata: dict[str, Any]


class SignalEngine:
    """
    Combines:

    - Confluence
    - Market Regime
    - Risk Management

    into one standardized analytical decision.

    No broker orders are executed here.
    """

    def __init__(
        self,
        minimum_confidence: float = 0.65,
        minimum_confluence: float = 0.60,
        minimum_risk_reward: float = 1.5,
    ) -> None:

        if not 0 <= minimum_confidence <= 1:
            raise ValueError(
                "minimum_confidence must be between 0 and 1."
            )

        if not 0 <= minimum_confluence <= 1:
            raise ValueError(
                "minimum_confluence must be between 0 and 1."
            )

        if minimum_risk_reward <= 0:
            raise ValueError(
                "minimum_risk_reward must be greater than zero."
            )

        self.minimum_confidence = (
            minimum_confidence
        )

        self.minimum_confluence = (
            minimum_confluence
        )

        self.minimum_risk_reward = (
            minimum_risk_reward
        )

    @staticmethod
    def _direction_to_score(
        direction: str,
    ) -> float:

        if direction == "bullish":
            return 1.0

        if direction == "bearish":
            return -1.0

        return 0.0

    def _calculate_strength(
        self,
        confluence: ConfluenceResult,
    ) -> float:

        bullish = (
            confluence.bullish_score
        )

        bearish = (
            confluence.bearish_score
        )

        neutral = (
            confluence.neutral_score
        )

        total = (
            bullish
            + bearish
            + neutral
        )

        if total <= 0:
            return 0.0

        if confluence.direction == "bullish":
            dominant = bullish
        elif confluence.direction == "bearish":
            dominant = bearish
        else:
            dominant = neutral

        return min(
            1.0,
            dominant / total,
        )

    def _regime_compatible(
        self,
        direction: str,
        regime: MarketRegime,
    ) -> bool:

        if direction == "bullish":
            return regime.regime == "trending_up"

        if direction == "bearish":
            return regime.regime == "trending_down"

        return regime.regime in {
            "ranging",
            "low_volatility",
            "transition",
        }

    def evaluate(
        self,
        confluence: ConfluenceResult,
        regime: MarketRegime,
        risk: RiskResult,
    ) -> SignalDecision:

        direction = (
            confluence.direction
        )

        strength = (
            self._calculate_strength(
                confluence
            )
        )

        confidence = (
            confluence.confidence
        )

        risk_reward = (
            risk.risk_reward_ratio
        )

        acceptable_risk = (
            risk_reward
            >= self.minimum_risk_reward
        )

        confluence_ok = (
            confluence.agreement
            >= self.minimum_confluence
        )

        confidence_ok = (
            confidence
            >= self.minimum_confidence
        )

        regime_ok = (
            self._regime_compatible(
                direction,
                regime,
            )
        )

        approved = (
            direction != "neutral"
            and confluence_ok
            and confidence_ok
            and regime_ok
            and acceptable_risk
        )

        reasons: list[str] = []

        reasons.extend(
            confluence.reasons
        )

        reasons.append(
            f"Market regime: "
            f"{regime.regime}"
        )

        reasons.append(
            f"Confluence agreement: "
            f"{confluence.agreement:.2%}"
        )

        reasons.append(
            f"Confidence: "
            f"{confidence:.2%}"
        )

        reasons.append(
            f"Risk/Reward: "
            f"{risk_reward:.2f}"
        )

        if not confluence_ok:
            reasons.append(
                "Confluence agreement is below threshold."
            )

        if not confidence_ok:
            reasons.append(
                "Confidence is below threshold."
            )

        if not regime_ok:
            reasons.append(
                "Market regime is not compatible with the direction."
            )

        if not acceptable_risk:
            reasons.append(
                "Risk/Reward ratio is below the required minimum."
            )

        return SignalDecision(
            direction=direction,
            strength=round(
                strength,
                4,
            ),
            confidence=round(
                confidence,
                4,
            ),
            regime=regime.regime,
            risk_reward_ratio=round(
                risk_reward,
                3,
            ),
            acceptable_risk=acceptable_risk,
            approved=approved,
            reasons=reasons,
            metadata={
                "confluence_direction":
                    confluence.direction,
                "bullish_score":
                    confluence.bullish_score,
                "bearish_score":
                    confluence.bearish_score,
                "neutral_score":
                    confluence.neutral_score,
                "agreement":
                    confluence.agreement,
                "regime_trend":
                    regime.trend,
                "regime_volatility":
                    regime.volatility,
                "regime_confidence":
                    regime.confidence,
            },
        )

    def summarize(
        self,
        decision: SignalDecision,
    ) -> dict[str, Any]:

        return {
            "direction":
                decision.direction,
            "strength":
                decision.strength,
            "confidence":
                decision.confidence,
            "regime":
                decision.regime,
            "risk_reward_ratio":
                decision.risk_reward_ratio,
            "acceptable_risk":
                decision.acceptable_risk,
            "approved":
                decision.approved,
            "reasons":
                decision.reasons,
            "metadata":
                decision.metadata,
        }
