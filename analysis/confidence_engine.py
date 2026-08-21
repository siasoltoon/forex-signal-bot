from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ==================================================
# Confidence Result
# ==================================================

@dataclass(frozen=True)
class ConfidenceResult:
    """
    Professional confidence evaluation result.

    Represents the reliability of the final market analysis.

    Includes:

    - Overall confidence
    - Engine agreement
    - Bullish / bearish / neutral votes
    - Weighted agreement
    - Conflict detection
    - Data quality
    - Market uncertainty
    - Confidence warnings
    """

    confidence: float

    agreement: float

    bullish_votes: int

    bearish_votes: int

    neutral_votes: int

    weighted_bullish: float = 0.0

    weighted_bearish: float = 0.0

    weighted_neutral: float = 0.0

    data_quality: float = 1.0

    market_uncertainty: float = 0.0

    conflict_score: float = 0.0

    warnings: list[str] = field(
        default_factory=list
    )


# ==================================================
# Confidence Engine
# ==================================================

class ConfidenceEngine:
    """
    Professional confidence evaluation engine.

    The engine evaluates the reliability of the final
    trading analysis rather than simply repeating the
    decision score.

    Evaluation layers:

    1. Engine agreement
    2. Weighted voting
    3. Directional consistency
    4. Conflict detection
    5. Data quality
    6. Market uncertainty
    7. Extreme score detection
    8. Confidence penalties

    Confidence range:

        0.0 -> 1.0
    """

    # ==================================================
    # Engine Weights
    # ==================================================

    WEIGHTS = {

        "smart_money": 2.00,

        "structure": 1.80,

        "price_action": 1.50,

        "momentum": 1.30,

        "supply_demand": 1.30,

        "candlestick": 1.10,

        "elliott": 1.00,

        "harmonic": 1.00,

        "brooks": 0.90,

        "wyckoff": 1.10,

    }

    # ==================================================
    # Direction Thresholds
    # ==================================================

    BULLISH_THRESHOLD = 55.0

    BEARISH_THRESHOLD = 45.0

    # ==================================================
    # Confidence Thresholds
    # ==================================================

    HIGH_AGREEMENT = 0.80

    MEDIUM_AGREEMENT = 0.60

    LOW_AGREEMENT = 0.50

    # ==================================================
    # Constructor
    # ==================================================

    def __init__(
        self,
        weights: dict[str, float] | None = None,
    ) -> None:

        self.weights = (
            weights.copy()
            if weights
            else self.WEIGHTS.copy()
        )

    # ==================================================
    # Normalize Score
    # ==================================================

    @staticmethod
    def normalize(
        score: float | None,
    ) -> float:
        """
        Converts an arbitrary score into
        the standard 0-100 range.
        """

        if score is None:
            return 50.0

        try:

            value = float(score)

        except (
            TypeError,
            ValueError,
        ):

            return 50.0

        return max(
            0.0,
            min(
                100.0,
                value,
            ),
        )

    # ==================================================
    # Normalize Confidence
    # ==================================================

    @staticmethod
    def normalize_confidence(
        value: float | None,
    ) -> float:
        """
        Converts confidence into 0-1 range.

        Supports:

            0.0 -> 1.0

        and percentage-like values:

            0 -> 100
        """

        if value is None:
            return 0.0

        try:

            value = float(value)

        except (
            TypeError,
            ValueError,
        ):

            return 0.0

        if value > 1.0:

            value /= 100.0

        return max(
            0.0,
            min(
                1.0,
                value,
            ),
        )

    # ==================================================
    # Convert Score To Direction
    # ==================================================

    @classmethod
    def direction(
        cls,
        score: float | None,
    ) -> str:
        """
        Converts a 0-100 score into direction.

        >= 55  -> bullish
        <= 45  -> bearish
        else   -> neutral
        """

        score = cls.normalize(
            score
        )

        if score >= cls.BULLISH_THRESHOLD:

            return "bullish"

        if score <= cls.BEARISH_THRESHOLD:

            return "bearish"

        return "neutral"

    # ==================================================
    # Direction Strength
    # ==================================================

    @classmethod
    def direction_strength(
        cls,
        score: float | None,
    ) -> float:
        """
        Measures how far the score is from
        the neutral midpoint.

        Returns:

            0.0 -> completely neutral
            1.0 -> maximum directional strength
        """

        score = cls.normalize(
            score
        )

        distance = abs(
            score - 50.0
        )

        return max(
            0.0,
            min(
                1.0,
                distance / 50.0,
            ),
        )

    # ==================================================
    # Safe Attribute
    # ==================================================

    @staticmethod
    def _get(
        analysis: Any,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Safely reads an analysis attribute.
        """

        try:

            return getattr(
                analysis,
                name,
                default,
            )

        except Exception:

            return default


    
    # ==================================================
    # Collect Engine Scores
    # ==================================================

    def _collect_engines(
        self,
        analysis: Any,
    ) -> dict[str, float]:
        """
        Collects scores from all available
        analysis engines.

        Missing engines default to neutral.
        """

        return {

            "smart_money": self.normalize(
                self._get(
                    analysis,
                    "smart_money_score",
                    50.0,
                )
            ),

            "structure": self.normalize(
                self._get(
                    analysis,
                    "structure_score",
                    50.0,
                )
            ),

            "price_action": self.normalize(
                self._get(
                    analysis,
                    "price_action_score",
                    50.0,
                )
            ),

            "momentum": self.normalize(
                self._get(
                    analysis,
                    "momentum_score",
                    50.0,
                )
            ),

            "supply_demand": self.normalize(
                self._get(
                    analysis,
                    "trend_score",
                    50.0,
                )
            ),

            "candlestick": self.normalize(
                self._get(
                    analysis,
                    "candlestick_score",
                    50.0,
                )
            ),

            "elliott": self.normalize(
                self._get(
                    analysis,
                    "elliott_score",
                    50.0,
                )
            ),

            "harmonic": self.normalize(
                self._get(
                    analysis,
                    "harmonic_score",
                    50.0,
                )
            ),

            "brooks": self.normalize(
                self._get(
                    analysis,
                    "brooks_score",
                    50.0,
                )
            ),

            "wyckoff": self.normalize(
                self._get(
                    analysis,
                    "wyckoff_score",
                    50.0,
                )
            ),
        }

    # ==================================================
    # Calculate Weighted Votes
    # ==================================================

    def _calculate_votes(
        self,
        engines: dict[str, float],
    ) -> tuple[
        int,
        int,
        int,
        float,
        float,
        float,
    ]:
        """
        Calculates weighted directional votes.

        Returns:

            bullish_votes
            bearish_votes
            neutral_votes
            weighted_bullish
            weighted_bearish
            weighted_neutral
        """

        bullish_votes = 0

        bearish_votes = 0

        neutral_votes = 0

        weighted_bullish = 0.0

        weighted_bearish = 0.0

        weighted_neutral = 0.0

        for (
            name,
            score,
        ) in engines.items():

            direction = self.direction(
                score
            )

            weight = float(
                self.weights.get(
                    name,
                    1.0,
                )
            )

            if weight <= 0:
                continue

            if direction == "bullish":

                bullish_votes += 1

                weighted_bullish += weight

            elif direction == "bearish":

                bearish_votes += 1

                weighted_bearish += weight

            else:

                neutral_votes += 1

                weighted_neutral += weight

        return (
            bullish_votes,
            bearish_votes,
            neutral_votes,
            weighted_bullish,
            weighted_bearish,
            weighted_neutral,
        )

    # ==================================================
    # Calculate Agreement
    # ==================================================

    @staticmethod
    def _calculate_agreement(
        weighted_bullish: float,
        weighted_bearish: float,
        weighted_neutral: float,
    ) -> float:
        """
        Calculates weighted model agreement.
        """

        total_weight = (
            weighted_bullish
            + weighted_bearish
            + weighted_neutral
        )

        if total_weight <= 0:

            return 0.0

        dominant_weight = max(
            weighted_bullish,
            weighted_bearish,
            weighted_neutral,
        )

        return max(
            0.0,
            min(
                1.0,
                dominant_weight / total_weight,
            ),
        )

    # ==================================================
    # Calculate Conflict
    # ==================================================

    @staticmethod
    def _calculate_conflict(
        weighted_bullish: float,
        weighted_bearish: float,
        total_weight: float,
    ) -> float:
        """
        Calculates directional conflict.

        0.0 = no conflict
        1.0 = maximum conflict
        """

        if total_weight <= 0:

            return 1.0

        directional_weight = (
            weighted_bullish
            + weighted_bearish
        )

        if directional_weight <= 0:

            return 0.0

        smaller_side = min(
            weighted_bullish,
            weighted_bearish,
        )

        return max(
            0.0,
            min(
                1.0,
                (
                    smaller_side
                    /
                    directional_weight
                ),
            ),
        )

    # ==================================================
    # Data Quality
    # ==================================================

    def _calculate_data_quality(
        self,
        analysis: Any,
    ) -> float:
        """
        Estimates the quality of available
        analysis data.

        Missing/invalid components reduce quality.
        """

        required_fields = (

            "smart_money_score",

            "structure_score",

            "price_action_score",

            "momentum_score",

            "elliott_score",

            "harmonic_score",

            "wyckoff_score",

        )

        available = 0

        total = len(
            required_fields
        )

        for field_name in required_fields:

            value = self._get(
                analysis,
                field_name,
                None,
            )

            if value is None:
                continue

            try:

                float(value)

                available += 1

            except (
                TypeError,
                ValueError,
            ):

                continue

        if total == 0:

            return 1.0

        return max(
            0.0,
            min(
                1.0,
                available / total,
            ),
        )

    # ==================================================
    # Market Uncertainty
    # ==================================================

    def _calculate_market_uncertainty(
        self,
        analysis: Any,
    ) -> float:
        """
        Estimates uncertainty from volatility
        and weak directional structure.
        """

        uncertainty = 0.0

        volatility_score = self.normalize(
            self._get(
                analysis,
                "volatility_score",
                0.0,
            )
        )

        if volatility_score >= 2.0:

            uncertainty += 0.15

        elif volatility_score >= 1.0:

            uncertainty += 0.05

        structure_score = self.normalize(
            self._get(
                analysis,
                "structure_score",
                50.0,
            )
        )

        if 45.0 < structure_score < 55.0:

            uncertainty += 0.15

        momentum_score = self.normalize(
            self._get(
                analysis,
                "momentum_score",
                50.0,
            )
        )

        if 45.0 < momentum_score < 55.0:

            uncertainty += 0.10

        return max(
            0.0,
            min(
                1.0,
                uncertainty,
            ),
        )

    # ==================================================
    # Build Warnings
    # ==================================================

    def _build_warnings(
        self,
        bullish_votes: int,
        bearish_votes: int,
        neutral_votes: int,
        agreement: float,
        conflict_score: float,
        data_quality: float,
        market_uncertainty: float,
    ) -> list[str]:
        """
        Creates human-readable confidence warnings.
        """

        warnings: list[str] = []

        total_votes = (
            bullish_votes
            + bearish_votes
            + neutral_votes
        )

        if (
            bullish_votes > 0
            and bearish_votes > 0
        ):

            warnings.append(
                "Analysis engines are directionally conflicting."
            )

        if neutral_votes >= 4:

            warnings.append(
                "Several analysis engines remain neutral."
            )

        if agreement < self.LOW_AGREEMENT:

            warnings.append(
                "Model agreement is low."
            )

        elif agreement < self.MEDIUM_AGREEMENT:

            warnings.append(
                "Model agreement is moderate."
            )

        if conflict_score >= 0.35:

            warnings.append(
                "Bullish and bearish evidence are significantly balanced."
            )

        if data_quality < 0.70:

            warnings.append(
                "Some analysis components contain insufficient data."
            )

        if market_uncertainty >= 0.25:

            warnings.append(
                "Current market conditions contain elevated uncertainty."
            )

        if total_votes == 0:

            warnings.append(
                "No valid analysis engine votes were available."
            )

        return warnings


    
    # ==================================================
    # Main Evaluation
    # ==================================================

    def evaluate(
        self,
        analysis: Any,
    ) -> ConfidenceResult:
        """
        Performs complete confidence evaluation.
        """

        # ==================================================
        # Collect Engine Scores
        # ==================================================

        engines = self._collect_engines(
            analysis
        )

        # ==================================================
        # Weighted Voting
        # ==================================================

        (
            bullish_votes,
            bearish_votes,
            neutral_votes,
            weighted_bullish,
            weighted_bearish,
            weighted_neutral,
        ) = self._calculate_votes(
            engines
        )

        # ==================================================
        # Agreement
        # ==================================================

        agreement = self._calculate_agreement(
            weighted_bullish,
            weighted_bearish,
            weighted_neutral,
        )

        # ==================================================
        # Conflict
        # ==================================================

        total_weight = (
            weighted_bullish
            + weighted_bearish
            + weighted_neutral
        )

        conflict_score = self._calculate_conflict(
            weighted_bullish,
            weighted_bearish,
            total_weight,
        )

        # ==================================================
        # Data Quality
        # ==================================================

        data_quality = self._calculate_data_quality(
            analysis
        )

        # ==================================================
        # Market Uncertainty
        # ==================================================

        market_uncertainty = (
            self._calculate_market_uncertainty(
                analysis
            )
        )

        # ==================================================
        # Base Confidence
        # ==================================================

        confidence = agreement

        # ==================================================
        # Conflict Penalty
        # ==================================================

        if conflict_score > 0.0:

            confidence *= (
                1.0
                -
                (
                    conflict_score
                    * 0.35
                )
            )

        # ==================================================
        # Data Quality Penalty
        # ==================================================

        confidence *= (
            0.70
            +
            (
                data_quality
                * 0.30
            )
        )

        # ==================================================
        # Market Uncertainty Penalty
        # ==================================================

        confidence *= (
            1.0
            -
            (
                market_uncertainty
                * 0.25
            )
        )

        # ==================================================
        # Decision Alignment
        # ==================================================

        decision_score = self.normalize(
            self._get(
                analysis,
                "decision_score",
                50.0,
            )
        )

        if decision_score != 50.0:

            decision_direction = self.direction(
                decision_score
            )

            directional_weights = {

                "bullish": weighted_bullish,

                "bearish": weighted_bearish,

                "neutral": weighted_neutral,

            }

            dominant_direction = max(
                directional_weights,
                key=directional_weights.get,
            )

            if (
                decision_direction != "neutral"
                and
                dominant_direction != "neutral"
                and
                decision_direction
                != dominant_direction
            ):

                confidence *= 0.85

        # ==================================================
        # Clamp Confidence
        # ==================================================

        confidence = max(
            0.0,
            min(
                1.0,
                confidence,
            ),
        )

        # ==================================================
        # Warnings
        # ==================================================

        warnings = self._build_warnings(
            bullish_votes=bullish_votes,
            bearish_votes=bearish_votes,
            neutral_votes=neutral_votes,
            agreement=agreement,
            conflict_score=conflict_score,
            data_quality=data_quality,
            market_uncertainty=market_uncertainty,
        )

        # ==================================================
        # Strong Conflict Warning
        # ==================================================

        if (
            bullish_votes >= 3
            and
            bearish_votes >= 3
        ):

            warnings.append(
                "Strong bullish and bearish disagreement detected."
            )

        # ==================================================
        # Very Low Confidence Warning
        # ==================================================

        if confidence < 0.40:

            warnings.append(
                "Overall confidence is too low for a high-conviction setup."
            )

        # ==================================================
        # High Confidence Validation
        # ==================================================

        if (
            confidence >= 0.80
            and
            agreement >= 0.80
            and
            conflict_score < 0.20
        ):

            warnings.append(
                "High multi-engine agreement detected."
            )

        # ==================================================
        # Return Result
        # ==================================================

        return ConfidenceResult(

            confidence=round(
                confidence,
                3,
            ),

            agreement=round(
                agreement,
                3,
            ),

            bullish_votes=bullish_votes,

            bearish_votes=bearish_votes,

            neutral_votes=neutral_votes,

            weighted_bullish=round(
                weighted_bullish,
                3,
            ),

            weighted_bearish=round(
                weighted_bearish,
                3,
            ),

            weighted_neutral=round(
                weighted_neutral,
                3,
            ),

            data_quality=round(
                data_quality,
                3,
            ),

            market_uncertainty=round(
                market_uncertainty,
                3,
            ),

            conflict_score=round(
                conflict_score,
                3,
            ),

            warnings=warnings,
        )
