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



    # =========================
    # Default Weights
    # =========================

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



    # =========================
    # Constructor
    # =========================

    def __init__(
        self,
        weights: dict[str, float] | None = None,
    ) -> None:

        self.weights = (
            weights
            if weights
            else self.WEIGHTS.copy()
        )



    # =========================
    # Main Decision
    # =========================

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
            analysis.smart_money_score
        )

        score += (
            smc_score
            *
            self.weights["smart_money"]
        )


        if analysis.smc_bias.lower() == "bullish":

            reasons.append(
                "Smart Money bullish bias"
            )

        elif analysis.smc_bias.lower() == "bearish":

            reasons.append(
                "Smart Money bearish bias"
            )



        # -------------------------
        # Structure
        # -------------------------

        structure_score = (
            analysis.structure_score
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

        score += (
            analysis.price_action_score
            *
            self.weights["price_action"]
        )


        if analysis.price_action_score > 0:

            reasons.append(
                "Price action confirmation"
            )



        # -------------------------
        # Supply Demand
        # -------------------------

        score += (
            analysis.trend_score
            *
            self.weights["supply_demand"]
        )



        # -------------------------
        # Indicators
        # -------------------------

        score += (
            analysis.momentum_score
            *
            self.weights["indicators"]
        )



        # -------------------------
        # Pattern Engines
        # -------------------------

        score += (
            analysis.elliott_score
            *
            self.weights["elliott"]
        )


        score += (
            analysis.harmonic_score
            *
            self.weights["harmonic"]
        )


        score += (
            analysis.wyckoff_score
            *
            self.weights["wyckoff"]
        )



        # =========================
        # Normalize Score
        # =========================

        score = max(
            0,
            min(
                100,
                score
            )
        )



        # =========================
        # Signal
        # =========================

        if score >= 80:

            signal = "STRONG BUY"


        elif score >= 60:

            signal = "BUY"


        elif score >= 40:

            signal = "NEUTRAL"


        elif score >= 20:

            signal = "SELL"


        else:

            signal = "STRONG SELL"



        # =========================
        # Confidence
        # =========================

        confidence = abs(
            score - 50
        ) * 2


        confidence = max(
            0,
            min(
                100,
                confidence
            )
        )



        # =========================
        # Bias
        # =========================

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
                2
            ),

            bias=bias,

            reasons=reasons,

        )
