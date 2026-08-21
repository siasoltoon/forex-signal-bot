from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any



# ==================================================
# Analysis Report
# ==================================================

@dataclass(
    frozen=True
)
class AnalysisReport:
    """
    Final user-facing analysis report.

    Contains:

    Core:
    - Trend
    - Structure
    - Score
    - Signal
    - Confidence

    Confidence:
    - Agreement
    - Votes
    - Warnings

    Smart Money:
    - Bias
    - Structure
    - Order Block
    - Liquidity
    - FVG

    Explanation:
    - Reasons
    - Indicators

    Future:
    - Risk Management
    - AI Layer
    """



    # ==================================================
    # Core Result
    # ==================================================

    trend: str


    structure: str


    score: float


    signal: str


    confidence: float



    # ==================================================
    # Confidence Layer
    # ==================================================

    agreement: float = 0.0


    bullish_votes: int = 0


    bearish_votes: int = 0


    neutral_votes: int = 0


    warnings: list[str] = field(

        default_factory=list

    )



    confidence_grade: str = "UNKNOWN"



    # ==================================================
    # Decision Layer
    # ==================================================

    decision_bias: str = "neutral"


    risk_level: str = "normal"



    # ==================================================
    # Smart Money Concepts
    # ==================================================

    smc_bias: str = "neutral"


    smc_structure: str = "unknown"


    order_block: dict[str, Any] | None = None


    liquidity: dict[str, Any] | None = None


    fair_value_gap: dict[str, Any] | None = None


    premium_discount: str = "unknown"


    
    # ==================================================
    # Explanation Layer
    # ==================================================

    reasons: list[str] = field(

        default_factory=list

    )



    # ==================================================
    # Indicators Snapshot
    # ==================================================

    indicators: dict[str, Any] = field(

        default_factory=dict

    )



    # ==================================================
    # Helper Methods
    # ==================================================

    def confidence_percentage(self) -> str:
        """
        Returns confidence as percentage.
        """

        value = int(

            self.confidence * 100

        )

        return f"{value}%"



    def confidence_label(self) -> str:
        """
        Converts confidence value
        into human readable label.
        """

        if self.confidence >= 0.85:

            return "VERY_HIGH"


        elif self.confidence >= 0.70:

            return "HIGH"


        elif self.confidence >= 0.50:

            return "MEDIUM"


        elif self.confidence >= 0.30:

            return "LOW"


        return "VERY_LOW"



    def vote_summary(self) -> dict[str, int]:
        """
        Returns engine vote summary.
        """

        return {

            "bullish": self.bullish_votes,

            "bearish": self.bearish_votes,

            "neutral": self.neutral_votes,

        }



    def is_strong_signal(self) -> bool:
        """
        Checks signal quality.
        """

        return (

            self.confidence >= 0.75

            and

            self.agreement >= 0.70

        )



    def summary(self) -> dict[str, Any]:
        """
        Compact report output.
        Useful for Telegram/API/AI layer.
        """

        return {

            "trend": self.trend,

            "structure": self.structure,

            "signal": self.signal,

            "score": self.score,

            "confidence": self.confidence_percentage(),

            "confidence_grade": self.confidence_label(),

            "agreement": self.agreement,

            "votes": self.vote_summary(),

            "risk": self.risk_level,

            "bias": self.decision_bias,

        }
