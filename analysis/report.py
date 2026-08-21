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

    Complete output model for:

    - Trading Bot
    - Telegram API
    - Web Dashboard
    - AI Explanation Layer
    """



    # ==================================================
    # Market Context
    # ==================================================

    symbol: str = "UNKNOWN"


    timeframe: str = "UNKNOWN"



    # ==================================================
    # Core Result
    # ==================================================

    trend: str = "neutral"


    structure: str = "unknown"


    score: float = 0.0


    signal: str = "NEUTRAL"


    confidence: float = 0.0



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
    # Risk Management Layer
    # ==================================================

    entry_price: float | None = None


    stop_loss: float | None = None


    take_profit: float | None = None


    risk_reward: float | None = None



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


    analysis_text: str = ""



    # ==================================================
    # Indicators Snapshot
    # ==================================================

    indicators: dict[str, Any] = field(

        default_factory=dict

    )



    # ==================================================
    # Helper Methods
    # ==================================================

    def confidence_percentage(
        self,
    ) -> str:
        """
        Returns confidence as percentage.
        """

        value = int(

            self.confidence * 100

        )

        return f"{value}%"



    def confidence_label(
        self,
    ) -> str:
        """
        Converts confidence value
        into readable grade.
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



    def vote_summary(
        self,
    ) -> dict[str, int]:
        """
        Returns engine votes.
        """

        return {

            "bullish": self.bullish_votes,

            "bearish": self.bearish_votes,

            "neutral": self.neutral_votes,

        }



    def is_strong_signal(
        self,
    ) -> bool:
        """
        Checks if signal has strong confirmation.
        """

        return (

            self.confidence >= 0.75

            and

            self.agreement >= 0.70

        )



    def has_risk_setup(
        self,
    ) -> bool:
        """
        Checks if trade management exists.
        """

        return (

            self.entry_price is not None

            and

            self.stop_loss is not None

            and

            self.take_profit is not None

        )



    def summary(
        self,
    ) -> dict[str, Any]:
        """
        Compact output for:

        - Telegram
        - API
        - AI layer
        """

        return {

            "symbol": self.symbol,

            "timeframe": self.timeframe,

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

            "entry": self.entry_price,

            "stop_loss": self.stop_loss,

            "take_profit": self.take_profit,

            "risk_reward": self.risk_reward,

        }
