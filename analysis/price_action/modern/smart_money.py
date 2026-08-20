from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class LiquidityLevel:
    price: float
    kind: str
    strength: float


@dataclass(frozen=True)
class FairValueGap:
    index: Any
    direction: str
    lower: float
    upper: float
    strength: float


@dataclass(frozen=True)
class OrderBlock:
    index: Any
    direction: str
    high: float
    low: float
    strength: float


class SmartMoneyAnalyzer:
    """
    Initial Smart Money / Modern Price Action engine.

    Detects:
    - Liquidity levels
    - Liquidity sweeps
    - Fair Value Gaps
    - Basic displacement candles
    - Basic order-block candidates

    These detections are contextual observations,
    not standalone trading signals.
    """

    def __init__(
        self,
        lookback: int = 20,
        displacement_multiplier: float = 1.5,
    ) -> None:

        if lookback < 3:
            raise ValueError(
                "lookback must be >= 3."
            )

        if displacement_multiplier <= 0:
            raise ValueError(
                "displacement_multiplier must be > 0."
            )

        self.lookback = lookback
        self.displacement_multiplier = (
            displacement_multiplier
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

    def detect_liquidity_levels(
        self,
        dataframe: pd.DataFrame,
    ) -> list[LiquidityLevel]:

        self._validate(dataframe)

        recent = dataframe.tail(
            self.lookback
        )

        levels: list[LiquidityLevel] = []

        highs = recent["high"]
        lows = recent["low"]

        if len(recent) < 3:
            return levels

        for i in range(
            1,
            len(recent) - 1,
        ):

            current_high = float(
                highs.iloc[i]
            )

            current_low = float(
                lows.iloc[i]
            )

            left_high = float(
                highs.iloc[i - 1]
            )

            right_high = float(
                highs.iloc[i + 1]
            )

            left_low = float(
                lows.iloc[i - 1]
            )

            right_low = float(
                lows.iloc[i + 1]
            )

            if (
                current_high > left_high
                and current_high > right_high
            ):
                levels.append(
                    LiquidityLevel(
                        price=current_high,
                        kind="buy_side",
                        strength=0.70,
                    )
                )

            if (
                current_low < left_low
                and current_low < right_low
            ):
                levels.append(
                    LiquidityLevel(
                        price=current_low,
                        kind="sell_side",
                        strength=0.70,
                    )
                )

        return levels

    def detect_liquidity_sweeps(
        self,
        dataframe: pd.DataFrame,
    ) -> list[dict[str, Any]]:

        self._validate(dataframe)

        sweeps: list[dict[str, Any]] = []

        if len(dataframe) < 4:
            return sweeps

        for i in range(
            2,
            len(dataframe),
        ):

            previous = dataframe.iloc[
                i - 2:i
            ]

            current = dataframe.iloc[i]

            previous_high = float(
                previous["high"].max()
            )

            previous_low = float(
                previous["low"].min()
            )

            current_high = float(
                current["high"]
            )

            current_low = float(
                current["low"]
            )

            current_close = float(
                current["close"]
            )

            index = dataframe.index[i]

            # Buy-side liquidity sweep:
            # price trades above previous highs
            # but closes back below them.
            if (
                current_high > previous_high
                and current_close < previous_high
            ):
                sweeps.append(
                    {
                        "index": index,
                        "type": "buy_side_sweep",
                        "level": previous_high,
                        "direction": "bearish",
                    }
                )

            # Sell-side liquidity sweep:
            # price trades below previous lows
            # but closes back above them.
            if (
                current_low < previous_low
                and current_close > previous_low
            ):
                sweeps.append(
                    {
                        "index": index,
                        "type": "sell_side_sweep",
                        "level": previous_low,
                        "direction": "bullish",
                    }
                )

        return sweeps

    def detect_fair_value_gaps(
        self,
        dataframe: pd.DataFrame,
    ) -> list[FairValueGap]:

        self._validate(dataframe)

        gaps: list[FairValueGap] = []

        if len(dataframe) < 3:
            return gaps

        for i in range(
            2,
            len(dataframe),
        ):

            first = dataframe.iloc[
                i - 2
            ]

            middle = dataframe.iloc[
                i - 1
            ]

            third = dataframe.iloc[i]

            # Bullish FVG:
            # third candle low > first candle high.
            if (
                float(third["low"])
                > float(first["high"])
            ):

                lower = float(
                    first["high"]
                )

                upper = float(
                    third["low"]
                )

                middle_range = (
                    self._candle_range(
                        middle
                    )
                )

                gap_size = upper - lower

                strength = min(
                    1.0,
                    gap_size
                    / middle_range,
                )

                gaps.append(
                    FairValueGap(
                        index=dataframe.index[i],
                        direction="bullish",
                        lower=lower,
                        upper=upper,
                        strength=strength,
                    )
                )

            # Bearish FVG:
            # third candle high < first candle low.
            if (
                float(third["high"])
                < float(first["low"])
            ):

                lower = float(
                    third["high"]
                )

                upper = float(
                    first["low"]
                )

                middle_range = (
                    self._candle_range(
                        middle
                    )
                )

                gap_size = upper - lower

                strength = min(
                    1.0,
                    gap_size
                    / middle_range,
                )

                gaps.append(
                    FairValueGap(
                        index=dataframe.index[i],
                        direction="bearish",
                        lower=lower,
                        upper=upper,
                        strength=strength,
                    )
                )

        return gaps

    def detect_displacement(
        self,
        dataframe: pd.DataFrame,
    ) -> list[dict[str, Any]]:

        self._validate(dataframe)

        if len(dataframe) < (
            self.lookback + 1
        ):
            return []

        ranges = (
            dataframe["high"]
            - dataframe["low"]
        )

        average_range = (
            ranges
            .rolling(self.lookback)
            .mean()
        )

        results: list[dict[str, Any]] = []

        for i in range(
            self.lookback,
            len(dataframe),
        ):

            row = dataframe.iloc[i]

            current_range = (
                float(row["high"])
                - float(row["low"])
            )

            average = float(
                average_range.iloc[i]
            )

            if average <= 0:
                continue

            if (
                current_range
                >= average
                * self.displacement_multiplier
            ):

                direction = (
                    "bullish"
                    if float(row["close"])
                    > float(row["open"])
                    else "bearish"
                )

                results.append(
                    {
                        "index": dataframe.index[i],
                        "direction": direction,
                        "range": current_range,
                        "average_range": average,
                        "strength": min(
                            1.0,
                            current_range
                            / (
                                average
                                * self.displacement_multiplier
                            ),
                        ),
                    }
                )

        return results

    def detect_order_blocks(
        self,
        dataframe: pd.DataFrame,
    ) -> list[OrderBlock]:

        self._validate(dataframe)

        blocks: list[OrderBlock] = []

        displacement = (
            self.detect_displacement(
                dataframe
            )
        )

        for event in displacement:

            index = event["index"]

            position = dataframe.index.get_loc(
                index
            )

            if position < 1:
                continue

            previous = dataframe.iloc[
                position - 1
            ]

            previous_open = float(
                previous["open"]
            )

            previous_close = float(
                previous["close"]
            )

            previous_high = float(
                previous["high"]
            )

            previous_low = float(
                previous["low"]
            )

            direction = event[
                "direction"
            ]

            # Bullish displacement after
            # a bearish candle.
            if (
                direction == "bullish"
                and previous_close
                < previous_open
            ):

                blocks.append(
                    OrderBlock(
                        index=dataframe.index[
                            position - 1
                        ],
                        direction="bullish",
                        high=previous_high,
                        low=previous_low,
                        strength=event[
                            "strength"
                        ],
                    )
                )

            # Bearish displacement after
            # a bullish candle.
            if (
                direction == "bearish"
                and previous_close
                > previous_open
            ):

                blocks.append(
                    OrderBlock(
                        index=dataframe.index[
                            position - 1
                        ],
                        direction="bearish",
                        high=previous_high,
                        low=previous_low,
                        strength=event[
                            "strength"
                        ],
                    )
                )

        return blocks

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        liquidity = (
            self.detect_liquidity_levels(
                dataframe
            )
        )

        sweeps = (
            self.detect_liquidity_sweeps(
                dataframe
            )
        )

        fvgs = (
            self.detect_fair_value_gaps(
                dataframe
            )
        )

        displacement = (
            self.detect_displacement(
                dataframe
            )
        )

        order_blocks = (
            self.detect_order_blocks(
                dataframe
            )
        )

        bullish_points = 0
        bearish_points = 0

        for sweep in sweeps[-5:]:

            if sweep["direction"] == "bullish":
                bullish_points += 2

            elif sweep["direction"] == "bearish":
                bearish_points += 2

        for fvg in fvgs[-5:]:

            if fvg.direction == "bullish":
                bullish_points += 1

            elif fvg.direction == "bearish":
                bearish_points += 1

        for block in order_blocks[-5:]:

            if block.direction == "bullish":
                bullish_points += 1

            elif block.direction == "bearish":
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
            "liquidity_levels": liquidity,
            "liquidity_sweeps": sweeps,
            "fair_value_gaps": fvgs,
            "displacement": displacement,
            "order_blocks": order_blocks,
        }
