from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class SwingPoint:
    """
    Represents a detected swing point.
    """

    index: object
    price: float
    kind: str


@dataclass(frozen=True)
class StructureEvent:
    """
    Represents a market-structure event.
    """

    event: str
    index: object
    price: float
    direction: str


class MarketStructureAnalyzer:
    """
    Detect basic market structure from OHLC data.

    The analyzer currently provides:
    - Swing highs
    - Swing lows
    - HH / HL / LH / LL
    - Basic trend state
    - Basic BOS / CHoCH detection
    """

    def __init__(
        self,
        swing_window: int = 2,
    ) -> None:

        if swing_window < 1:
            raise ValueError(
                "swing_window must be >= 1."
            )

        self.swing_window = swing_window

    def _validate_data(
        self,
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

        if len(dataframe) < (
            self.swing_window * 2 + 1
        ):
            raise ValueError(
                "Not enough candles for swing detection."
            )

    def detect_swings(
        self,
        dataframe: pd.DataFrame,
    ) -> list[SwingPoint]:

        self._validate_data(dataframe)

        window = self.swing_window

        swings: list[SwingPoint] = []

        highs = dataframe["high"]
        lows = dataframe["low"]

        for i in range(
            window,
            len(dataframe) - window,
        ):

            current_high = highs.iloc[i]
            current_low = lows.iloc[i]

            left_highs = highs.iloc[
                i - window:i
            ]

            right_highs = highs.iloc[
                i + 1:i + window + 1
            ]

            left_lows = lows.iloc[
                i - window:i
            ]

            right_lows = lows.iloc[
                i + 1:i + window + 1
            ]

            is_swing_high = (
                current_high > left_highs.max()
                and current_high > right_highs.max()
            )

            is_swing_low = (
                current_low < left_lows.min()
                and current_low < right_lows.min()
            )

            index = dataframe.index[i]

            if is_swing_high:
                swings.append(
                    SwingPoint(
                        index=index,
                        price=float(
                            current_high
                        ),
                        kind="high",
                    )
                )

            if is_swing_low:
                swings.append(
                    SwingPoint(
                        index=index,
                        price=float(
                            current_low
                        ),
                        kind="low",
                    )
                )

        return swings

    def classify_swings(
        self,
        swings: list[SwingPoint],
    ) -> list[SwingPoint]:

        highs = [
            swing
            for swing in swings
            if swing.kind == "high"
        ]

        lows = [
            swing
            for swing in swings
            if swing.kind == "low"
        ]

        classified: list[SwingPoint] = []

        previous_high: Optional[float] = None
        previous_low: Optional[float] = None

        for swing in swings:

            if swing.kind == "high":

                if previous_high is None:
                    label = "H"

                elif swing.price > previous_high:
                    label = "HH"

                else:
                    label = "LH"

                previous_high = swing.price

            else:

                if previous_low is None:
                    label = "L"

                elif swing.price > previous_low:
                    label = "HL"

                else:
                    label = "LL"

                previous_low = swing.price

            classified.append(
                SwingPoint(
                    index=swing.index,
                    price=swing.price,
                    kind=label,
                )
            )

        return classified

    def detect_trend(
        self,
        classified_swings: list[SwingPoint],
    ) -> str:

        labels = [
            swing.kind
            for swing in classified_swings
        ]

        bullish_score = (
            labels.count("HH")
            + labels.count("HL")
        )

        bearish_score = (
            labels.count("LH")
            + labels.count("LL")
        )

        if bullish_score > bearish_score:
            return "bullish"

        if bearish_score > bullish_score:
            return "bearish"

        return "range"

    def detect_structure_events(
        self,
        dataframe: pd.DataFrame,
        classified_swings: list[SwingPoint],
    ) -> list[StructureEvent]:

        if dataframe.empty:
            return []

        events: list[StructureEvent] = []

        last_swing_high: Optional[
            SwingPoint
        ] = None

        last_swing_low: Optional[
            SwingPoint
        ] = None

        previous_trend: Optional[str] = None

        for i in range(len(dataframe)):

            index = dataframe.index[i]

            close = float(
                dataframe["close"].iloc[i]
            )

            current_swings = [
                swing
                for swing in classified_swings
                if swing.index == index
            ]

            for swing in current_swings:

                if swing.kind in (
                    "H",
                    "HH",
                    "LH",
                ):
                    last_swing_high = swing

                elif swing.kind in (
                    "L",
                    "HL",
                    "LL",
                ):
                    last_swing_low = swing

            trend = None

            if last_swing_high:
                if close > last_swing_high.price:
                    trend = "bullish"

            if last_swing_low:
                if close < last_swing_low.price:
                    trend = "bearish"

            if trend is None:
                continue

            if previous_trend is None:

                previous_trend = trend

                events.append(
                    StructureEvent(
                        event="BOS",
                        index=index,
                        price=close,
                        direction=trend,
                    )
                )

                continue

            if trend != previous_trend:

                events.append(
                    StructureEvent(
                        event="CHoCH",
                        index=index,
                        price=close,
                        direction=trend,
                    )
                )

                previous_trend = trend

            else:

                events.append(
                    StructureEvent(
                        event="BOS",
                        index=index,
                        price=close,
                        direction=trend,
                    )
                )

        return events

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict:

        swings = self.detect_swings(
            dataframe
        )

        classified = self.classify_swings(
            swings
        )

        trend = self.detect_trend(
            classified
        )

        events = self.detect_structure_events(
            dataframe,
            classified,
        )

        return {
            "trend": trend,
            "swings": classified,
            "events": events,
        }
