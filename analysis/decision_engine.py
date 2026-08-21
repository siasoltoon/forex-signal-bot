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
    Final trading decision.
    """

    signal: str

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
    and creates final decision.
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

            weights

            if weights

            else self.WEIGHTS.copy()

        )



    # ==================================================
    # Main Decision
    # ==================================================

    def decide(
        self,
        analysis: Any,
    ) -> DecisionResult:


        score = 0.0

        reasons = []



        # -------------------------
        # Smart Money
        # -------------------------

        smc_score = (

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



        if smc_bias.lower() == "bullish":

            reasons.append(
                "Smart Money bullish bias"
            )


        elif smc_bias.lower() == "bearish":

            reasons.append(
                "Smart Money bearish bias"
            )



        # -------------------------
        # Structure
        # -------------------------

        structure_score = getattr(
            analysis,
            "structure_score",
            0.0
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



        # -------------------------
        # Price Action
        # -------------------------

        price_action_score = getattr(
            analysis,
            "price_action_score",
            0.0
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


        # -------------------------
        # Supply Demand
        # -------------------------

        score += (

            getattr(
                analysis,
                "trend_score",
                0.0
            )

            *

            self.weights["supply_demand"]

        )



        # -------------------------
        # Indicators
        # -------------------------

        score += (

            getattr(
                analysis,
                "momentum_score",
                0.0
            )

            *

            self.weights["indicators"]

        )



        # -------------------------
        # Pattern Engines
        # -------------------------

        score += (

            getattr(
                analysis,
                "elliott_score",
                0.0
            )

            *

            self.weights["elliott"]

        )


        score += (

            getattr(
                analysis,
                "harmonic_score",
                0.0
            )

            *

            self.weights["harmonic"]

        )


        score += (

            getattr(
                analysis,
                "wyckoff_score",
                0.0
            )

            *

            self.weights["wyckoff"]

        )



        # ==================================================
        # Normalize Score
        # ==================================================

        score = max(

            0,

            min(

                100,

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
        # Confidence
        # ==================================================

        confidence = abs(

            score - 50

        ) / 50



        confidence = max(

            0,

            min(

                1,

                confidence

            )

        )



        # ==================================================
        # Bias
        # ==================================================

        if score >= 50:

            bias = "bullish"

        else:

            bias = "bearish"



        return DecisionResult(

            signal=signal,


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
