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
    Evaluates reliability of final analysis.

    Checks:

    - Engine agreement
    - Conflicts
    - Market uncertainty
    """



    def __init__(
        self,
    ) -> None:

        pass



    # ==================================================
    # Convert Score To Direction
    # ==================================================

    @staticmethod
    def direction(
        score: float,
    ) -> str:

        if score > 55:

            return "bullish"


        elif score < 45:

            return "bearish"


        return "neutral"



    # ==================================================
    # Main Calculation
    # ==================================================

    def evaluate(
        self,
        analysis: Any,
    ) -> ConfidenceResult:


        bullish_votes = 0

        bearish_votes = 0

        neutral_votes = 0


        warnings: list[str] = []



        # ==========================
        # Collect Analysis Engines
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

                float(score)

            )


            if state == "bullish":

                bullish_votes += 1



            elif state == "bearish":

                bearish_votes += 1



            else:

                neutral_votes += 1


      
        # ==========================
        # Agreement Calculation
        # ==========================

        total_votes = (

            bullish_votes

            +

            bearish_votes

            +

            neutral_votes

        )



        if total_votes == 0:

            agreement = 0.0


        else:

            strongest_vote = max(

                bullish_votes,

                bearish_votes,

                neutral_votes

            )


            agreement = (

                strongest_vote

                /

                total_votes

            )



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

                "Low agreement between analysis models"

            )



        # ==========================
        # Final Confidence
        # ==========================

        confidence = agreement



        # Conflict penalty

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
        # Return Result
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
