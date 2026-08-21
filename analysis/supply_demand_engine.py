from __future__ import annotations

from dataclasses import dataclass



@dataclass(
    frozen=True
)
class SupplyDemandResult:
    """
    Supply and Demand analysis result.
    """

    zone: str

    score: float

    strength: float

    reason: str



class SupplyDemandEngine:
    """
    Detects basic supply and demand zones.

    Logic:
    - Demand:
        Strong upward reaction after a drop

    - Supply:
        Strong downward reaction after a rise

    Future upgrades:
    - Fresh zones
    - Mitigation
    - Order blocks
    - Liquidity sweep
    - Smart Money Concepts
    """



    def analyze(
        self,
        closes: list[float],
    ) -> SupplyDemandResult:


        if len(closes) < 5:

            return SupplyDemandResult(
                zone="neutral",
                score=0,
                strength=0,
                reason="Not enough price data.",
            )



        recent = closes[-5:]


        first = recent[0]

        last = recent[-1]



        change = (
            last - first
        )



        # =====================
        # Demand Zone
        # =====================

        if change > 0:


            strength = min(
                abs(change) * 100,
                100,
            )


            return SupplyDemandResult(
                zone="demand",

                score=20,

                strength=strength,

                reason=(
                    "Demand zone detected. "
                    "Buyers pushed price higher."
                ),
            )



        # =====================
        # Supply Zone
        # =====================

        if change < 0:


            strength = min(
                abs(change) * 100,
                100,
            )


            return SupplyDemandResult(
                zone="supply",

                score=-20,

                strength=strength,

                reason=(
                    "Supply zone detected. "
                    "Sellers pushed price lower."
                ),
            )



        return SupplyDemandResult(
            zone="neutral",

            score=0,

            strength=0,

            reason="No clear supply or demand zone.",
        )
