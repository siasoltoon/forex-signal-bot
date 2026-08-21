from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any



# ==================================================
# Confidence Result
# ==================================================

@dataclass(
    frozen=True
)
class ConfidenceResult:
    """
    Result of confidence evaluation.
    """

    confidence: float

    agreement: float

    bullish_votes: int

    bearish_votes: int

    neutral_votes: int

    warnings: list[str] = field(
        default_factory=list
    )



# ==================================================
# Confidence Engine
# ==================================================

class ConfidenceEngine:
    """
    Evaluates reliability of analysis.

    Uses:
    - Engine agreement
    - Weighted voting
    - Conflict detection
    - Market uncertainty
    """



    WEIGHTS = {

        "smart_money": 2.0,

        "structure": 1.5,

        "price_action": 1.3,

        "momentum": 1.2,

        "elliott": 1.0,

        "harmonic": 1.0,

        "wyckoff": 1.0,

    }



    def __init__(
        self,
    ) -> None:

        pass



    # ==================================================
    # Normalize Score
    # ==================================================

    @staticmethod
    def normalize(
        score: float,
    ) -> float:

        return max(

            0.0,

            min(

                100.0,

                float(score)

            )

        )



    # ==================================================
    # Convert Score To Direction
    # ==================================================

    @staticmethod
    def direction(
        score: float,
    ) -> str:


        score = ConfidenceEngine.normalize(
            score
        )


        if score >= 55:

            return "bullish"


        elif score <= 45:

            return "bearish"


        return "neutral"


    
    # ==================================================
    # Main Evaluation
    # ==================================================

    def evaluate(
        self,
        analysis: Any,
    ) -> ConfidenceResult:


        bullish_votes = 0

        bearish_votes = 0

        neutral_votes = 0


        weighted_bullish = 0.0

        weighted_bearish = 0.0

        weighted_neutral = 0.0


        warnings: list[str] = []



        # ==========================
        # Collect Engines
        # ==========================

        engines = {


            "smart_money": getattr(

                analysis,

                "smart_money_score",

                50

            ),


            "structure": getattr(

                analysis,

                "structure_score",

                50

            ),


            "price_action": getattr(

                analysis,

                "price_action_score",

                50

            ),


            "momentum": getattr(

                analysis,

                "momentum_score",

                50

            ),


            "elliott": getattr(

                analysis,

                "elliott_score",

                50

            ),


            "harmonic": getattr(

                analysis,

                "harmonic_score",

                50

            ),


            "wyckoff": getattr(

                analysis,

                "wyckoff_score",

                50

            ),

        }



        # ==========================
        # Vote Calculation
        # ==========================

        for name, score in engines.items():


            state = self.direction(

                score

            )


            weight = self.WEIGHTS.get(

                name,

                1.0

            )



            if state == "bullish":

                bullish_votes += 1

                weighted_bullish += weight



            elif state == "bearish":

                bearish_votes += 1

                weighted_bearish += weight



            else:

                neutral_votes += 1

                weighted_neutral += weight





        total_weight = (

            weighted_bullish

            +

            weighted_bearish

            +

            weighted_neutral

        )



        if total_weight == 0:

            agreement = 0.0


        else:

            agreement = max(

                weighted_bullish,

                weighted_bearish,

                weighted_neutral

            ) / total_weight





        # ==========================
        # Conflict Detection
        # ==========================


        if (

            bullish_votes > 0

            and

            bearish_votes > 0

        ):

            warnings.append(

                "Analysis engines are conflicting"

            )



        if neutral_votes >= 4:

            warnings.append(

                "Market direction is unclear"

            )



        if agreement < 0.5:

            warnings.append(

                "Low model agreement"

            )



        if (

            bullish_votes >= 5

            and

            bearish_votes >= 2

        ):

            warnings.append(

                "Strong bullish/bearish disagreement detected"

            )



        # ==========================
        # Final Confidence
        # ==========================


        confidence = agreement



        if (

            bullish_votes > 0

            and

            bearish_votes > 0

        ):

            confidence *= 0.75



        confidence = max(

            0.0,

            min(

                1.0,

                confidence

            )

        )



        # ==========================
        # Return
        # ==========================

        return ConfidenceResult(


            confidence=round(

                confidence,

                3

            ),


            agreement=round(

                agreement,

                3

            ),


            bullish_votes=bullish_votes,


            bearish_votes=bearish_votes,


            neutral_votes=neutral_votes,


            warnings=warnings,

        )
