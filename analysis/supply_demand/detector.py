from __future__ import annotations

from analysis.supply_demand.models import (
    PriceZone,
    SupplyDemandResult,
)


class SupplyDemandDetector:
    """
    Detect supply and demand zones.

    Detects:
    - Supply zones
    - Demand zones
    - Zone strength
    - Fresh zones
    """


    def analyze(
        self,
        candles: list[dict[str, float]],
    ) -> SupplyDemandResult:
        """
        Analyze candles and find zones.
        """

        self._validate_candles(
            candles
        )


        supply_zones = []

        demand_zones = []


        for index in range(
            1,
            len(candles) - 1,
        ):

            previous = candles[index - 1]

            current = candles[index]

            next_candle = candles[index + 1]


            # Rally -> Drop
            if (
                current["high"] > previous["high"]
                and next_candle["close"]
                <
                current["open"]
            ):

                supply_zones.append(
                    PriceZone(
                        zone_type="supply",
                        high=current["high"],
                        low=current["low"],
                        strength=0.7,
                        touches=0,
                        fresh=True,
                    )
                )


            # Drop -> Rally
            if (
                current["low"] < previous["low"]
                and next_candle["close"]
                >
                current["open"]
            ):

                demand_zones.append(
                    PriceZone(
                        zone_type="demand",
                        high=current["high"],
                        low=current["low"],
                        strength=0.7,
                        touches=0,
                        fresh=True,
                    )
                )


        return SupplyDemandResult(
            supply_zones=supply_zones,
            demand_zones=demand_zones,
        )



    @staticmethod
    def _validate_candles(
        candles: list[dict[str, float]],
    ) -> None:

        if not isinstance(
            candles,
            list,
        ):
            raise TypeError(
                "candles must be a list."
            )


        if len(candles) < 3:
            raise ValueError(
                "At least 3 candles required."
            )


        for candle in candles:

            required = {
                "open",
                "high",
                "low",
                "close",
            }


            if not required.issubset(
                candle.keys()
            ):
                raise ValueError(
                    "Invalid candle format."
                )
