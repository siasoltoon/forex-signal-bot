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
    Combines all analysis modules
    and creates final trading decision.
    """



    WEIGHTS = {

        "smart_money": 0.25,

        "structure": 0.20,

        "price_action": 0.15,

        "supply_demand": 0.15,

        "indicators": 0.10,

        "elliott": 0.05,

        "harmonic": 0.05,

        "wyckoff": 0.05,

    }



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
    # Helpers
    # ==================================================

    @staticmethod
    def normalize_component(
        value: float
    ) -> float:
        """
        Convert any score into 0-100 range.
        """

        if value is None:

            return 0.0


        value = float(value)


        if value < 0:

            value = 0


        if value > 100:

            value = 100


        return value



    # ==================================================
    # Main Decision
    # ==================================================

    def decide(
        self,
        analysis: Any,
    ) -> DecisionResult:


        score = 0.0


        reasons: list[str] = []



        # ==================================================
        # Smart Money Concepts
        # ==================================================

        smc_score = self.normalize_component(

            getattr(
                analysis,
                "smart_money_score",
                0.0
            )

        )


        score += (

            smc_score

            *

            self.weights["smart_money"]

        )



        smc_bias = getattr(

            analysis,

            "smc_bias",

            "neutral"

        )



        if isinstance(
            smc_bias,
            str
        ):


            if smc_bias.lower() == "bullish":

                reasons.append(
                    "Smart Money bullish bias"
                )


            elif smc_bias.lower() == "bearish":

                reasons.append(
                    "Smart Money bearish bias"
                )



        # ==================================================
        # Market Structure
        # ==================================================

        structure_score = self.normalize_component(

            getattr(
                analysis,
                "structure_score",
                0.0
            )

        )


        score += (

            structure_score

            *

            self.weights["structure"]

        )



        if structure_score > 0:

            reasons.append(

                "Market structure confirmation"

            )



        # ==================================================
        # Price Action
        # ==================================================

        price_action_score = self.normalize_component(

            getattr(
                analysis,
                "price_action_score",
                0.0
            )

        )


        score += (

            price_action_score

            *

            self.weights["price_action"]

        )



        if price_action_score > 0:

            reasons.append(

                "Price action confirmation"

            )

        

        # ==================================================
        # Supply Demand
        # ==================================================

        supply_score = self.normalize_component(

            getattr(
                analysis,
                "trend_score",
                0.0
            )

        )


        score += (

            supply_score

            *

            self.weights["supply_demand"]

        )



        if supply_score > 0:

            reasons.append(

                "Supply Demand confirmation"

            )



        # ==================================================
        # Indicators / Momentum
        # ==================================================

        indicator_score = self.normalize_component(

            getattr(
                analysis,
                "momentum_score",
                0.0
            )

        )


        score += (

            indicator_score

            *

            self.weights["indicators"]

        )



        if indicator_score > 0:

            reasons.append(

                "Momentum confirmation"

            )



        # ==================================================
        # Pattern Engines
        # ==================================================

        elliott_score = self.normalize_component(

            getattr(
                analysis,
                "elliott_score",
                0.0
            )

        )


        harmonic_score = self.normalize_component(

            getattr(
                analysis,
                "harmonic_score",
                0.0
            )

        )


        wyckoff_score = self.normalize_component(

            getattr(
                analysis,
                "wyckoff_score",
                0.0
            )

        )



        score += (

            elliott_score

            *

            self.weights["elliott"]

        )


        score += (

            harmonic_score

            *

            self.weights["harmonic"]

        )


        score += (

            wyckoff_score

            *

            self.weights["wyckoff"]

        )



        # ==================================================
        # Final Score
        # ==================================================

        score = max(

            0.0,

            min(

                100.0,

                score

            )

        )



        # ==================================================
        # Signal
        # ==================================================

        if score >= 60:

            signal = "BUY"


        elif score <= 40:

            signal = "SELL"


        else:

            signal = "NEUTRAL"



        # ==================================================
        # Signal Strength
        # ==================================================

        if score >= 80 or score <= 20:

            strength = "STRONG"


        elif score >= 60 or score <= 40:

            strength = "MODERATE"


        else:

            strength = "WEAK"



        # ==================================================
        # Confidence
        # ==================================================

        confidence = abs(

            score - 50

        ) / 50



        confidence = max(

            0.0,

            min(

                1.0,

                confidence

            )

        )



        # ==================================================
        # Bias
        # ==================================================

        if score > 50:

            bias = "bullish"


        elif score < 50:

            bias = "bearish"


        else:

            bias = "neutral"



        # ==================================================
        # Final Reasons
        # ==================================================

        reasons.append(

            f"Final score: {round(score,2)}"

        )


        reasons.append(

            f"Confidence: {round(confidence,3)}"

        )



        return DecisionResult(

            signal=signal,

            strength=strength,

            score=round(

                score,

                2

            ),

            confidence=round(

                confidence,

                3

            ),

            bias=bias,

            reasons=reasons,

        )
