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

        self._validate_candles(
            candles
        )

        supply_zones: list[PriceZone] = []

        demand_zones: list[PriceZone] = []


        for index in range(
            1,
            len(candles) - 1,
        ):

            previous = candles[index - 1]
            current = candles[index]
            next_candle = candles[index + 1]


            # -------------------------
            # Supply
            # Rally -> Drop
            # -------------------------

            if (
                previous["close"] < current["close"]
                and
                next_candle["close"] < current["close"]
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


            # -------------------------
            # Demand
            # Drop -> Rally
            # -------------------------

            if (
                previous["close"] > current["close"]
                and
                next_candle["close"] > current["close"]
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


        required = {
            "open",
            "high",
            "low",
            "close",
        }


        for candle in candles:

            if not required.issubset(
                candle.keys()
            ):
                raise ValueError(
                    "Invalid candle format."
                )
