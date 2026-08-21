
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from analysis.candle import Candle


# ==================================================
# Signal Component
# ==================================================

@dataclass(
    frozen=True
)
class SignalComponent:
    """
    Single analysis/scoring component.

    Represents one independent analytical contribution.
    """

    name: str

    score: float

    reason: str

    direction: str = "neutral"

    weight: float = 1.0

    confidence: float = 0.0


# ==================================================
# Analysis Score
# ==================================================

@dataclass(
    frozen=True
)
class AnalysisScore:
    """
    Aggregated scoring result.

    Contains:

    - Final score
    - Direction
    - Confidence
    - Individual components
    """

    score: float

    direction: str

    confidence: float

    components: list[SignalComponent] = field(
        default_factory=list
    )

    # ==================================================
    # Helpers
    # ==================================================

    def is_bullish(self) -> bool:
        """
        Returns True when the score direction is bullish.
        """

        return self.direction.lower() == "bullish"

    def is_bearish(self) -> bool:
        """
        Returns True when the score direction is bearish.
        """

        return self.direction.lower() == "bearish"

    def is_neutral(self) -> bool:
        """
        Returns True when the score direction is neutral.
        """

        return self.direction.lower() == "neutral"


# ==================================================
# Complete Analysis Result
# ==================================================

@dataclass(
    frozen=True
)
class AnalysisResult:
    """
    Complete internal technical-analysis state.

    This object is the central data contract between:

    - Market Structure
    - Indicators
    - Momentum
    - Price Action
    - Supply / Demand
    - Candlestick
    - Elliott Wave
    - Harmonic
    - Brooks
    - Wyckoff
    - Smart Money Concepts
    - Decision Engine
    - Confidence Engine
    - Future AI layers
    """

    # ==================================================
    # Core Analysis
    # ==================================================

    trend: str = "neutral"

    momentum: str = "neutral"

    indicators: dict[str, Any] = field(
        default_factory=dict
    )

    candles: list[Candle] = field(
        default_factory=list
    )

    # ==================================================
    # Market Context
    # ==================================================

    symbol: str = "UNKNOWN"

    timeframe: str = "UNKNOWN"

    current_price: float | None = None

    # ==================================================
    # Supply / Demand
    # ==================================================

    supply_demand: Any = None

    # ==================================================
    # Core Scores
    # ==================================================

    trend_score: float = 0.0

    momentum_score: float = 0.0

    structure_score: float = 0.0

    volatility_score: float = 0.0

    price_action_score: float = 0.0

    # ==================================================
    # Pattern Scores
    # ==================================================

    candlestick_score: float = 0.0

    elliott_score: float = 0.0

    harmonic_score: float = 0.0

    brooks_score: float = 0.0

    wyckoff_score: float = 0.0

    # ==================================================
    # Smart Money Concepts
    # ==================================================

    smart_money_score: float = 0.0

    smc_bias: str = "neutral"

    smc_structure: str = "unknown"

    order_block: dict[str, Any] | None = None

    liquidity: dict[str, Any] | None = None

    fair_value_gap: dict[str, Any] | None = None

    premium_discount: str = "unknown"

    # ==================================================
    # Additional SMC Metrics
    # ==================================================

    liquidity_score: float = 0.0

    # ==================================================
    # AI Layer
    # ==================================================

    ai_score: float = 0.0

    ai_confidence: float = 0.0

    ai_direction: str = "neutral"

    ai_reasons: list[str] = field(
        default_factory=list
    )

    # ==================================================
    # Aggregated Score
    # ==================================================

    total_score: float = 0.0

    final_direction: str = "neutral"

    # ==================================================
    # Explanation
    # ==================================================

    reasons: list[str] = field(
        default_factory=list
    )

    warnings: list[str] = field(
        default_factory=list
    )

    # ==================================================
    # Helpers
    # ==================================================

    def score_components(
        self,
    ) -> dict[str, float]:
        """
        Returns all major analytical scores.
        """

        return {
            "trend": self.trend_score,
            "momentum": self.momentum_score,
            "structure": self.structure_score,
            "volatility": self.volatility_score,
            "price_action": self.price_action_score,
            "candlestick": self.candlestick_score,
            "elliott": self.elliott_score,
            "harmonic": self.harmonic_score,
            "brooks": self.brooks_score,
            "wyckoff": self.wyckoff_score,
            "smart_money": self.smart_money_score,
            "liquidity": self.liquidity_score,
            "ai": self.ai_score,
        }

    def is_bullish(self) -> bool:
        """
        Returns True when the final direction is bullish.
        """

        return self.final_direction.lower() == "bullish"

    def is_bearish(self) -> bool:
        """
        Returns True when the final direction is bearish.
        """

        return self.final_direction.lower() == "bearish"

    def is_neutral(self) -> bool:
        """
        Returns True when the final direction is neutral.
        """

        return self.final_direction.lower() == "neutral"

    def has_smc_data(self) -> bool:
        """
        Checks whether meaningful SMC information exists.
        """

        return any(
            (
                self.smc_bias != "neutral",
                self.smc_structure != "unknown",
                self.order_block is not None,
                self.liquidity is not None,
                self.fair_value_gap is not None,
            )
        )

    def has_ai_data(self) -> bool:
        """
        Checks whether the AI layer has produced information.
        """

        return (
            self.ai_score != 0.0
            or self.ai_confidence != 0.0
            or self.ai_direction != "neutral"
            or bool(self.ai_reasons)
        )



    # ==================================================
    # Risk Context
    # ==================================================

    def latest_candle(
        self,
    ) -> Candle | None:
        """
        Returns the latest candle when available.
        """

        if not self.candles:
            return None

        return self.candles[-1]

    # ==================================================
    # Indicator Helpers
    # ==================================================

    def get_indicator(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Safely retrieves an indicator value.
        """

        return self.indicators.get(
            name,
            default,
        )

    # ==================================================
    # Reason Management
    # ==================================================

    def all_reasons(
        self,
    ) -> list[str]:
        """
        Returns all available analytical explanations.

        Combines:

        - General reasons
        - AI reasons
        - Warnings
        """

        result: list[str] = []

        for reason in self.reasons:
            if reason:
                result.append(
                    str(reason)
                )

        for reason in self.ai_reasons:
            if reason:
                result.append(
                    str(reason)
                )

        for warning in self.warnings:
            if warning:
                result.append(
                    f"Warning: {warning}"
                )

        return result

    # ==================================================
    # Summary
    # ==================================================

    def summary(
        self,
    ) -> dict[str, Any]:
        """
        Returns a serializable compact representation
        of the analysis state.

        Useful for:

        - Decision Engine
        - Confidence Engine
        - Telegram
        - API
        - Dashboard
        - AI layer
        """

        return {
            "symbol": self.symbol,

            "timeframe": self.timeframe,

            "current_price": self.current_price,

            "trend": self.trend,

            "momentum": self.momentum,

            "scores": self.score_components(),

            "total_score": self.total_score,

            "final_direction": self.final_direction,

            "smc": {
                "score": self.smart_money_score,
                "bias": self.smc_bias,
                "structure": self.smc_structure,
                "order_block": self.order_block,
                "liquidity": self.liquidity,
                "fair_value_gap": self.fair_value_gap,
                "premium_discount": self.premium_discount,
            },

            "ai": {
                "score": self.ai_score,
                "confidence": self.ai_confidence,
                "direction": self.ai_direction,
                "reasons": self.ai_reasons,
            },

            "supply_demand": self.supply_demand,

            "indicators": self.indicators,

            "reasons": self.reasons,

            "warnings": self.warnings,
        }


# ==================================================
# Validation Helpers
# ==================================================

def clamp_score(
    value: float,
) -> float:
    """
    Restricts a score to the standard 0-100 range.
    """

    try:
        numeric_value = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return 0.0

    return round(
        max(
            0.0,
            min(
                100.0,
                numeric_value,
            ),
        ),
        2,
    )


def clamp_confidence(
    value: float,
) -> float:
    """
    Restricts confidence to 0.0-1.0.
    """

    try:
        numeric_value = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return 0.0

    return round(
        max(
            0.0,
            min(
                1.0,
                numeric_value,
            ),
        ),
        3,
    )


def normalize_direction(
    direction: str | None,
) -> str:
    """
    Normalizes common directional values.
    """

    if not direction:
        return "neutral"

    value = str(
        direction
    ).strip().lower()

    if value in {
        "buy",
        "bull",
        "bullish",
        "long",
        "up",
    }:
        return "bullish"

    if value in {
        "sell",
        "bear",
        "bearish",
        "short",
        "down",
    }:
        return "bearish"

    return "neutral"



