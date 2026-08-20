from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class SupplyDemandZone:
    index: Any
    zone_type: str
    high: float
    low: float
    strength: float
    status: str
    touches: int


class SupplyDemandAnalyzer:
    """
    Supply & Demand zone detection engine.

    Detects:
    - Supply zones
    - Demand zones
    - Fresh zones
    - Tested zones
    - Mitigated zones

    The output is contextual analysis and is not
    a standalone trading signal.
    """

    def __init__(
        self,
        lookback: int = 50,
        impulse_multiplier: float = 1.5,
    ) -> None:

        if lookback < 5:
            raise ValueError(
                "lookback must be >= 5."
            )

        if impulse_multiplier <= 0:
            raise ValueError(
                "impulse_multiplier must be > 0."
            )

        self.lookback = lookback
        self.impulse_multiplier = (
            impulse_multiplier
        )

    @staticmethod
    def _validate(
        dataframe: pd.DataFrame,
    ) -> None:

        required = [
            "open",
            "high",
            "low",
            "close",
        ]

        missing = [
            column
            for column in required
            if column not in dataframe.columns
        ]

        if missing:
            raise ValueError(
                f"Missing columns: {missing}"
            )

        if dataframe.empty:
            raise ValueError(
                "DataFrame cannot be empty."
            )

    @staticmethod
    def _candle_range(
        row: pd.Series,
    ) -> float:

        return max(
            float(row["high"])
            - float(row["low"]),
            1e-12,
        )

    def _average_range(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.Series:

        ranges = (
            dataframe["high"]
            - dataframe["low"]
        )

        return ranges.rolling(
            self.lookback
        ).mean()

    def detect_zones(
        self,
        dataframe: pd.DataFrame,
    ) -> list[SupplyDemandZone]:

        self._validate(dataframe)

        if len(dataframe) < (
            self.lookback + 3
        ):
            return []

        average_ranges = (
            self._average_range(
                dataframe
            )
        )

        zones: list[
            SupplyDemandZone
        ] = []

        for i in range(
            self.lookback,
            len(dataframe) - 1,
        ):

            base = dataframe.iloc[i]

            next_candle = dataframe.iloc[
                i + 1
            ]

            average_range = float(
                average_ranges.iloc[i]
            )

            if average_range <= 0:
                continue

            base_range = (
                self._candle_range(base)
            )

            next_range = (
                self._candle_range(
                    next_candle
                )
            )

            next_open = float(
                next_candle["open"]
            )

            next_close = float(
                next_candle["close"]
            )

            base_open = float(
                base["open"]
            )

            base_close = float(
                base["close"]
            )

            # ----------------------------------
            # Demand candidate
            # ----------------------------------

            bullish_impulse = (
                next_close > next_open
                and next_range
                >= average_range
                * self.impulse_multiplier
            )

            base_bearish = (
                base_close < base_open
            )

            if (
                bullish_impulse
                and base_bearish
            ):

                zone_high = float(
                    base["high"]
                )

                zone_low = float(
                    base["low"]
                )

                strength = min(
                    1.0,
                    next_range
                    / (
                        average_range
                        * self.impulse_multiplier
                    ),
                )

                zones.append(
                    SupplyDemandZone(
                        index=dataframe.index[i],
                        zone_type="demand",
                        high=zone_high,
                        low=zone_low,
                        strength=strength,
                        status="fresh",
                        touches=0,
                    )
                )

            # ----------------------------------
            # Supply candidate
            # ----------------------------------

            bearish_impulse = (
                next_close < next_open
                and next_range
                >= average_range
                * self.impulse_multiplier
            )

            base_bullish = (
                base_close > base_open
            )

            if (
                bearish_impulse
                and base_bullish
            ):

                zone_high = float(
                    base["high"]
                )

                zone_low = float(
                    base["low"]
                )

                strength = min(
                    1.0,
                    next_range
                    / (
                        average_range
                        * self.impulse_multiplier
                    ),
                )

                zones.append(
                    SupplyDemandZone(
                        index=dataframe.index[i],
                        zone_type="supply",
                        high=zone_high,
                        low=zone_low,
                        strength=strength,
                        status="fresh",
                        touches=0,
                    )
                )

        return zones

    def evaluate_zone_status(
        self,
        dataframe: pd.DataFrame,
        zone: SupplyDemandZone,
    ) -> SupplyDemandZone:

        self._validate(dataframe)

        zone_position = dataframe.index.get_loc(
            zone.index
        )

        future_data = dataframe.iloc[
            zone_position + 1:
        ]

        touches = 0
        mitigated = False

        for _, candle in future_data.iterrows():

            high = float(
                candle["high"]
            )

            low = float(
                candle["low"]
            )

            close = float(
                candle["close"]
            )

            intersects = (
                high >= zone.low
                and low <= zone.high
            )

            if intersects:
                touches += 1

            # Demand invalidation
            if zone.zone_type == "demand":

                if close < zone.low:
                    mitigated = True
                    break

            # Supply invalidation
            elif zone.zone_type == "supply":

                if close > zone.high:
                    mitigated = True
                    break

        if mitigated:
            status = "mitigated"

        elif touches == 0:
            status = "fresh"

        else:
            status = "tested"

        return SupplyDemandZone(
            index=zone.index,
            zone_type=zone.zone_type,
            high=zone.high,
            low=zone.low,
            strength=zone.strength,
            status=status,
            touches=touches,
        )

    def evaluate_zones(
        self,
        dataframe: pd.DataFrame,
        zones: list[
            SupplyDemandZone
        ],
    ) -> list[SupplyDemandZone]:

        evaluated = []

        for zone in zones:

            evaluated.append(
                self.evaluate_zone_status(
                    dataframe,
                    zone,
                )
            )

        return evaluated

    def get_active_zones(
        self,
        zones: list[
            SupplyDemandZone
        ],
    ) -> list[SupplyDemandZone]:

        return [
            zone
            for zone in zones
            if zone.status
            != "mitigated"
        ]

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        zones = self.detect_zones(
            dataframe
        )

        zones = self.evaluate_zones(
            dataframe,
            zones,
        )

        active_zones = (
            self.get_active_zones(
                zones
            )
        )

        demand_zones = [
            zone
            for zone in active_zones
            if zone.zone_type
            == "demand"
        ]

        supply_zones = [
            zone
            for zone in active_zones
            if zone.zone_type
            == "supply"
        ]

        current_price = float(
            dataframe["close"].iloc[-1]
        )

        nearby_demand = [
            zone
            for zone in demand_zones
            if zone.low
            <= current_price
            <= zone.high
            or current_price
            >= zone.low
        ]

        nearby_supply = [
            zone
            for zone in supply_zones
            if zone.low
            <= current_price
            <= zone.high
            or current_price
            <= zone.high
        ]

        bullish_points = 0
        bearish_points = 0

        for zone in nearby_demand[-5:]:

            if zone.status == "fresh":
                bullish_points += 2

            elif zone.status == "tested":
                bullish_points += 1

        for zone in nearby_supply[-5:]:

            if zone.status == "fresh":
                bearish_points += 2

            elif zone.status == "tested":
                bearish_points += 1

        if bullish_points > bearish_points:
            bias = "bullish"

        elif bearish_points > bullish_points:
            bias = "bearish"

        else:
            bias = "neutral"

        return {
            "bias": bias,
            "bullish_points": bullish_points,
            "bearish_points": bearish_points,
            "zones": zones,
            "active_zones": active_zones,
            "demand_zones": demand_zones,
            "supply_zones": supply_zones,
        }
