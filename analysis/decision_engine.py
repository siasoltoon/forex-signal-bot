from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ==================================================
# Decision Result
# ==================================================

@dataclass(
    frozen=True
)
class DecisionResult:
    """
    Final trading decision result.

    Output of the decision layer.

    score:
        Final directional score from 0 to 100.

        0   = extremely bearish
        50  = neutral
        100 = extremely bullish

    confidence:
        Decision confidence from 0.0 to 1.0.
    """

    signal: str

    strength: str

    score: float

    confidence: float

    bias: str

    reasons: list[str]


# ==================================================
# Decision Engine
# ==================================================

class DecisionEngine:
    """
    Professional multi-engine decision engine.

    Combines:

    - Smart Money Concepts
    - Market Structure
    - Price Action
    - Supply / Demand
    - Indicators / Momentum
    - Elliott Wave
    - Harmonic Patterns
    - Wyckoff
    - Candlestick
    - Brooks / Al Brooks style analysis

    The engine preserves directional information.

    Final score:

        0   -> strongly bearish
        50  -> neutral
        100 -> strongly bullish
    """

    # ==================================================
    # Default Weights
    # ==================================================

    DEFAULT_WEIGHTS: dict[str, float] = {

        "smart_money": 0.20,

        "structure": 0.15,

        "price_action": 0.15,

        "supply_demand": 0.10,

        "indicators": 0.10,

        "candlestick": 0.08,

        "elliott": 0.06,

        "harmonic": 0.05,

        "brooks": 0.05,

        "wyckoff": 0.06,

    }

    # ==================================================
    # Signal Thresholds
    # ==================================================

    STRONG_BUY_THRESHOLD = 80.0

    BUY_THRESHOLD = 60.0

    SELL_THRESHOLD = 40.0

    STRONG_SELL_THRESHOLD = 20.0

    # ==================================================
    # Constructor
    # ==================================================

    def __init__(
        self,
        weights: dict[str, float] | None = None,
        buy_threshold: float = BUY_THRESHOLD,
        sell_threshold: float = SELL_THRESHOLD,
        strong_buy_threshold: float = STRONG_BUY_THRESHOLD,
        strong_sell_threshold: float = STRONG_SELL_THRESHOLD,
    ) -> None:

        self.weights = self._prepare_weights(
            weights
        )

        self.buy_threshold = float(
            buy_threshold
        )

        self.sell_threshold = float(
            sell_threshold
        )

        self.strong_buy_threshold = float(
            strong_buy_threshold
        )

        self.strong_sell_threshold = float(
            strong_sell_threshold
        )

        self._validate_thresholds()

    # ==================================================
    # Weight Preparation
    # ==================================================

    def _prepare_weights(
        self,
        weights: dict[str, float] | None,
    ) -> dict[str, float]:
        """
        Creates and validates the engine weights.

        Custom weights are merged with defaults,
        so missing engines still receive their
        default weight.
        """

        result = self.DEFAULT_WEIGHTS.copy()

        if weights:

            for key, value in weights.items():

                if key not in result:
                    continue

                try:

                    numeric_value = float(
                        value
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    continue

                if numeric_value < 0:
                    continue

                result[key] = numeric_value

        total = sum(
            result.values()
        )

        if total <= 0:

            return self.DEFAULT_WEIGHTS.copy()

        return {
            key: value / total
            for key, value in result.items()
        }

    # ==================================================
    # Threshold Validation
    # ==================================================

    def _validate_thresholds(
        self,
    ) -> None:

        if not (
            0.0
            <= self.strong_sell_threshold
            < self.sell_threshold
            < self.buy_threshold
            < self.strong_buy_threshold
            <= 100.0
        ):

            raise ValueError(
                "Invalid decision thresholds."
            )

    # ==================================================
    # Numeric Safety
    # ==================================================

    @staticmethod
    def _safe_float(
        value: Any,
        default: float = 0.0,
    ) -> float:
        """
        Safely converts a value to float.
        """

        if value is None:
            return default

        try:

            result = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return default

        if result != result:
            return default

        return result

    # ==================================================
    # Clamp
    # ==================================================

    @staticmethod
    def _clamp(
        value: float,
        minimum: float,
        maximum: float,
    ) -> float:

        return max(
            minimum,
            min(
                maximum,
                value,
            ),
        )

    # ==================================================
    # Normalize Signed Score
    # ==================================================

    @classmethod
    def normalize_signed_component(
        cls,
        value: float | None,
    ) -> float:
        """
        Converts a directional score from:

            -100 ... +100

        into:

            0 ... 100

        Examples:

            -100 -> 0
             -50 -> 25
               0 -> 50
             +50 -> 75
            +100 -> 100

        This is important because the old engine
        converted negative values directly to zero,
        destroying bearish information.
        """

        numeric_value = cls._safe_float(
            value
        )

        numeric_value = cls._clamp(
            numeric_value,
            -100.0,
            100.0,
        )

        return (
            numeric_value
            + 100.0
        ) / 2.0

    # ==================================================
    # Normalize 0-100 Score
    # ==================================================

    @classmethod
    def normalize_component(
        cls,
        value: float | None,
    ) -> float:
        """
        Normalizes a score already expected
        to be in the 0-100 range.

        Values outside the range are clamped.
        """

        numeric_value = cls._safe_float(
            value
        )

        return cls._clamp(
            numeric_value,
            0.0,
            100.0,
        )

    # ==================================================
    # Read Component
    # ==================================================

    @classmethod
    def _read_component(
        cls,
        analysis: Any,
        attribute: str,
        default: float = 0.0,
    ) -> float:
        """
        Safely reads an analysis component.
        """

        return cls._safe_float(
            getattr(
                analysis,
                attribute,
                default,
            ),
            default,
        )


    
    # ==================================================
    # Component Direction
    # ==================================================

    @staticmethod
    def _direction_from_score(
        score: float,
    ) -> str:
        """
        Converts a 0-100 score into direction.
        """

        if score > 55.0:

            return "bullish"

        if score < 45.0:

            return "bearish"

        return "neutral"

    # ==================================================
    # Add Component
    # ==================================================

    def _apply_component(
        self,
        total: float,
        analysis_score: float,
        weight: float,
        reasons: list[str],
        name: str,
        bullish_reason: str,
        bearish_reason: str,
        neutral_reason: str | None = None,
    ) -> float:
        """
        Applies one analysis component to
        the final weighted score.
        """

        component_score = (
            self.normalize_signed_component(
                analysis_score
            )
        )

        total += (
            component_score
            * weight
        )

        direction = (
            self._direction_from_score(
                component_score
            )
        )

        if direction == "bullish":

            reasons.append(
                bullish_reason
            )

        elif direction == "bearish":

            reasons.append(
                bearish_reason
            )

        elif neutral_reason:

            reasons.append(
                neutral_reason
            )

        return total

    # ==================================================
    # Smart Money
    # ==================================================

    def _apply_smart_money(
        self,
        total: float,
        analysis: Any,
        reasons: list[str],
    ) -> float:

        score = self._read_component(
            analysis,
            "smart_money_score",
        )

        total = self._apply_component(
            total=total,
            analysis_score=score,
            weight=self.weights[
                "smart_money"
            ],
            reasons=reasons,
            name="Smart Money",
            bullish_reason=(
                "Smart Money Concepts "
                "support a bullish scenario"
            ),
            bearish_reason=(
                "Smart Money Concepts "
                "support a bearish scenario"
            ),
            neutral_reason=(
                "Smart Money Concepts "
                "are currently neutral"
            ),
        )

        smc_bias = getattr(
            analysis,
            "smc_bias",
            "neutral",
        )

        if isinstance(
            smc_bias,
            str,
        ):

            smc_bias = smc_bias.lower().strip()

            if smc_bias == "bullish":

                reasons.append(
                    "SMC bias is bullish"
                )

            elif smc_bias == "bearish":

                reasons.append(
                    "SMC bias is bearish"
                )

        return total

    # ==================================================
    # Market Structure
    # ==================================================

    def _apply_structure(
        self,
        total: float,
        analysis: Any,
        reasons: list[str],
    ) -> float:

        structure_score = (
            self._read_component(
                analysis,
                "structure_score",
            )
        )

        trend_score = (
            self._read_component(
                analysis,
                "trend_score",
            )
        )

        # Structure and trend are combined.
        #
        # This avoids relying only on BOS,
        # because the FullAnalysisEngine can
        # provide trend direction separately.

        combined_score = (
            structure_score
            + trend_score
        ) / 2.0

        total = self._apply_component(
            total=total,
            analysis_score=combined_score,
            weight=self.weights[
                "structure"
            ],
            reasons=reasons,
            name="Market Structure",
            bullish_reason=(
                "Market structure favors buyers"
            ),
            bearish_reason=(
                "Market structure favors sellers"
            ),
            neutral_reason=(
                "Market structure is balanced"
            ),
        )

        trend = getattr(
            analysis,
            "trend",
            "neutral",
        )

        if isinstance(
            trend,
            str,
        ):

            trend = trend.lower().strip()

            if trend == "bullish":

                reasons.append(
                    "Higher-level market trend is bullish"
                )

            elif trend == "bearish":

                reasons.append(
                    "Higher-level market trend is bearish"
                )

        return total

    # ==================================================
    # Price Action
    # ==================================================

    def _apply_price_action(
        self,
        total: float,
        analysis: Any,
        reasons: list[str],
    ) -> float:

        score = self._read_component(
            analysis,
            "price_action_score",
        )

        return self._apply_component(
            total=total,
            analysis_score=score,
            weight=self.weights[
                "price_action"
            ],
            reasons=reasons,
            name="Price Action",
            bullish_reason=(
                "Price action confirms bullish pressure"
            ),
            bearish_reason=(
                "Price action confirms bearish pressure"
            ),
            neutral_reason=(
                "Price action does not provide "
                "a strong directional edge"
            ),
        )

    # ==================================================
    # Supply Demand
    # ==================================================

    def _apply_supply_demand(
        self,
        total: float,
        analysis: Any,
        reasons: list[str],
    ) -> float:

        score = self._read_component(
            analysis,
            "trend_score",
        )

        supply_demand = getattr(
            analysis,
            "supply_demand",
            None,
        )

        total = self._apply_component(
            total=total,
            analysis_score=score,
            weight=self.weights[
                "supply_demand"
            ],
            reasons=reasons,
            name="Supply Demand",
            bullish_reason=(
                "Supply/Demand conditions favor demand"
            ),
            bearish_reason=(
                "Supply/Demand conditions favor supply"
            ),
            neutral_reason=(
                "Supply/Demand conditions are neutral"
            ),
        )

        if supply_demand:

            reasons.append(
                f"Supply/Demand zone: {supply_demand}"
            )

        return total

    # ==================================================
    # Indicators / Momentum
    # ==================================================

    def _apply_indicators(
        self,
        total: float,
        analysis: Any,
        reasons: list[str],
    ) -> float:

        score = self._read_component(
            analysis,
            "momentum_score",
        )

        return self._apply_component(
            total=total,
            analysis_score=score,
            weight=self.weights[
                "indicators"
            ],
            reasons=reasons,
            name="Indicators",
            bullish_reason=(
                "Momentum and indicators support buyers"
            ),
            bearish_reason=(
                "Momentum and indicators support sellers"
            ),
            neutral_reason=(
                "Momentum is not strongly directional"
            ),
        )

    # ==================================================
    # Candlestick
    # ==================================================

    def _apply_candlestick(
        self,
        total: float,
        analysis: Any,
        reasons: list[str],
    ) -> float:

        score = self._read_component(
            analysis,
            "candlestick_score",
        )

        return self._apply_component(
            total=total,
            analysis_score=score,
            weight=self.weights[
                "candlestick"
            ],
            reasons=reasons,
            name="Candlestick",
            bullish_reason=(
                "Candlestick structure supports bullish continuation/reversal"
            ),
            bearish_reason=(
                "Candlestick structure supports bearish continuation/reversal"
            ),
            neutral_reason=(
                "Candlestick signals are inconclusive"
            ),
        )

    # ==================================================
    # Elliott
    # ==================================================

    def _apply_elliott(
        self,
        total: float,
        analysis: Any,
        reasons: list[str],
    ) -> float:

        score = self._read_component(
            analysis,
            "elliott_score",
        )

        return self._apply_component(
            total=total,
            analysis_score=score,
            weight=self.weights[
                "elliott"
            ],
            reasons=reasons,
            name="Elliott",
            bullish_reason=(
                "Elliott analysis favors bullish structure"
            ),
            bearish_reason=(
                "Elliott analysis favors bearish structure"
            ),
            neutral_reason=(
                "Elliott wave structure is inconclusive"
            ),
        )

    # ==================================================
    # Harmonic
    # ==================================================

    def _apply_harmonic(
        self,
        total: float,
        analysis: Any,
        reasons: list[str],
    ) -> float:

        score = self._read_component(
            analysis,
            "harmonic_score",
        )

        return self._apply_component(
            total=total,
            analysis_score=score,
            weight=self.weights[
                "harmonic"
            ],
            reasons=reasons,
            name="Harmonic",
            bullish_reason=(
                "Harmonic analysis supports bullish conditions"
            ),
            bearish_reason=(
                "Harmonic analysis supports bearish conditions"
            ),
            neutral_reason=(
                "No strong harmonic directional confirmation"
            ),
        )

    # ==================================================
    # Brooks
    # ==================================================

    def _apply_brooks(
        self,
        total: float,
        analysis: Any,
        reasons: list[str],
    ) -> float:

        score = self._read_component(
            analysis,
            "brooks_score",
        )

        return self._apply_component(
            total=total,
            analysis_score=score,
            weight=self.weights[
                "brooks"
            ],
            reasons=reasons,
            name="Brooks",
            bullish_reason=(
                "Brooks price-action analysis favors bulls"
            ),
            bearish_reason=(
                "Brooks price-action analysis favors bears"
            ),
            neutral_reason=(
                "Brooks analysis is currently balanced"
            ),
        )

    # ==================================================
    # Wyckoff
    # ==================================================

    def _apply_wyckoff(
        self,
        total: float,
        analysis: Any,
        reasons: list[str],
    ) -> float:

        score = self._read_component(
            analysis,
            "wyckoff_score",
        )

        return self._apply_component(
            total=total,
            analysis_score=score,
            weight=self.weights[
                "wyckoff"
            ],
            reasons=reasons,
            name="Wyckoff",
            bullish_reason=(
                "Wyckoff structure favors accumulation/markup"
            ),
            bearish_reason=(
                "Wyckoff structure favors distribution/markdown"
            ),
            neutral_reason=(
                "Wyckoff structure is inconclusive"
            ),
        )


    
    # ==================================================
    # Calculate Final Score
    # ==================================================

    def _calculate_final_score(
        self,
        analysis: Any,
        reasons: list[str],
    ) -> float:
        """
        Calculates the weighted final score.
        """

        score = 0.0

        score = self._apply_smart_money(
            score,
            analysis,
            reasons,
        )

        score = self._apply_structure(
            score,
            analysis,
            reasons,
        )

        score = self._apply_price_action(
            score,
            analysis,
            reasons,
        )

        score = self._apply_supply_demand(
            score,
            analysis,
            reasons,
        )

        score = self._apply_indicators(
            score,
            analysis,
            reasons,
        )

        score = self._apply_candlestick(
            score,
            analysis,
            reasons,
        )

        score = self._apply_elliott(
            score,
            analysis,
            reasons,
        )

        score = self._apply_harmonic(
            score,
            analysis,
            reasons,
        )

        score = self._apply_brooks(
            score,
            analysis,
            reasons,
        )

        score = self._apply_wyckoff(
            score,
            analysis,
            reasons,
        )

        return round(
            self._clamp(
                score,
                0.0,
                100.0,
            ),
            2,
        )

    # ==================================================
    # Signal
    # ==================================================

    def _calculate_signal(
        self,
        score: float,
    ) -> str:

        if score >= self.buy_threshold:

            return "BUY"

        if score <= self.sell_threshold:

            return "SELL"

        return "NEUTRAL"

    # ==================================================
    # Strength
    # ==================================================

    def _calculate_strength(
        self,
        score: float,
    ) -> str:

        if (
            score >= self.strong_buy_threshold
            or
            score <= self.strong_sell_threshold
        ):

            return "STRONG"

        if (
            score >= self.buy_threshold
            or
            score <= self.sell_threshold
        ):

            return "MODERATE"

        return "WEAK"

    # ==================================================
    # Bias
    # ==================================================

    @staticmethod
    def _calculate_bias(
        score: float,
    ) -> str:

        if score > 50.0:

            return "bullish"

        if score < 50.0:

            return "bearish"

        return "neutral"

    # ==================================================
    # Confidence
    # ==================================================

    @classmethod
    def _calculate_confidence(
        cls,
        score: float,
    ) -> float:
        """
        Converts distance from the neutral midpoint
        into a confidence value.

        50 -> 0.00
        60 -> 0.20
        75 -> 0.50
        90 -> 0.80
        100 -> 1.00
        """

        distance = abs(
            score - 50.0
        )

        confidence = (
            distance / 50.0
        )

        return round(
            cls._clamp(
                confidence,
                0.0,
                1.0,
            ),
            3,
        )

    # ==================================================
    # Confidence Adjustment
    # ==================================================

    @classmethod
    def _adjust_confidence_for_neutrality(
        cls,
        confidence: float,
        score: float,
    ) -> float:
        """
        Prevents overconfidence around the
        neutral decision zone.
        """

        if (
            45.0 <= score <= 55.0
        ):

            confidence *= 0.50

        return round(
            cls._clamp(
                confidence,
                0.0,
                1.0,
            ),
            3,
        )

    # ==================================================
    # Final Reasons
    # ==================================================

    @staticmethod
    def _build_final_reasons(
        reasons: list[str],
        score: float,
        confidence: float,
        signal: str,
        strength: str,
        bias: str,
    ) -> list[str]:

        final_reasons = list(
            reasons
        )

        final_reasons.append(
            f"Final decision score: {score:.2f}/100"
        )

        final_reasons.append(
            f"Decision signal: {signal}"
        )

        final_reasons.append(
            f"Signal strength: {strength}"
        )

        final_reasons.append(
            f"Directional bias: {bias}"
        )

        final_reasons.append(
            f"Decision confidence: {confidence:.3f}"
        )

        return final_reasons

    # ==================================================
    # Main Decision
    # ==================================================

    def decide(
        self,
        analysis: Any,
    ) -> DecisionResult:
        """
        Generates the final trading decision.

        Parameters
        ----------
        analysis:
            AnalysisResult produced by FullAnalysisEngine.

        Returns
        -------
        DecisionResult
        """

        reasons: list[str] = []

        # --------------------------------------------------
        # Calculate weighted score
        # --------------------------------------------------

        score = self._calculate_final_score(
            analysis,
            reasons,
        )

        # --------------------------------------------------
        # Signal
        # --------------------------------------------------

        signal = self._calculate_signal(
            score
        )

        # --------------------------------------------------
        # Strength
        # --------------------------------------------------

        strength = self._calculate_strength(
            score
        )

        # --------------------------------------------------
        # Bias
        # --------------------------------------------------

        bias = self._calculate_bias(
            score
        )

        # --------------------------------------------------
        # Confidence
        # --------------------------------------------------

        confidence = self._calculate_confidence(
            score
        )

        confidence = (
            self._adjust_confidence_for_neutrality(
                confidence,
                score,
            )
        )

        # --------------------------------------------------
        # Final reasons
        # --------------------------------------------------

        reasons = self._build_final_reasons(
            reasons=reasons,
            score=score,
            confidence=confidence,
            signal=signal,
            strength=strength,
            bias=bias,
        )

        # --------------------------------------------------
        # Return
        # --------------------------------------------------

        return DecisionResult(

            signal=signal,

            strength=strength,

            score=score,

            confidence=confidence,

            bias=bias,

            reasons=reasons,

        )
