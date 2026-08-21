from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from analysis.candle import Candle


# ==================================================
# Swing Point
# ==================================================

@dataclass(frozen=True)
class SwingPoint:
    """
    Represents a detected market swing.

    kind can be:

    H
    L
    HH
    HL
    LH
    LL
    """

    index: object

    price: float

    kind: str


# ==================================================
# Structure Event
# ==================================================

@dataclass(frozen=True)
class StructureEvent:
    """
    Represents a market structure event.

    event:

    BOS
    CHoCH

    direction:

    bullish
    bearish
    """

    event: str

    index: object

    price: float

    direction: str


# ==================================================
# Market Structure Result
# ==================================================

@dataclass(frozen=True)
class MarketStructureResult:
    """
    Final market structure analysis result.

    Designed to work directly with
    FullAnalysisEngine.
    """

    trend: str

    structure: str

    bos: bool

    choch: bool

    bos_direction: str

    choch_direction: str

    swings: list[SwingPoint]

    events: list[StructureEvent]

    last_swing_high: float | None

    last_swing_low: float | None


# ==================================================
# Market Structure Detector
# ==================================================

class MarketStructureDetector:
    """
    Professional market structure detector.

    Detects:

    - Swing High
    - Swing Low
    - HH
    - HL
    - LH
    - LL
    - BOS
    - CHoCH
    - Bullish trend
    - Bearish trend
    - Range
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


    # ==================================================
    # Build DataFrame From Candles
    # ==================================================

    @staticmethod
    def _candles_to_dataframe(
        candles: list[Candle],
    ) -> pd.DataFrame:

        if not candles:

            raise ValueError(
                "Candles cannot be empty."
            )

        rows = []

        for candle in candles:

            rows.append(
                {
                    "open": float(candle.open),

                    "high": float(candle.high),

                    "low": float(candle.low),

                    "close": float(candle.close),

                    "volume": float(
                        getattr(
                            candle,
                            "volume",
                            0.0,
                        )
                    ),
                }
            )

        return pd.DataFrame(rows)


    # ==================================================
    # Build DataFrame From Prices
    # ==================================================

    @staticmethod
    def _prices_to_dataframe(
        prices: list[float],
    ) -> pd.DataFrame:

        if not prices:

            raise ValueError(
                "Prices cannot be empty."
            )

        values = [
            float(price)
            for price in prices
        ]

        return pd.DataFrame(
            {
                "open": values,

                "high": values,

                "low": values,

                "close": values,

                "volume": [0.0] * len(values),
            }
        )


    # ==================================================
    # Validate Data
    # ==================================================

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

        minimum_length = (
            self.swing_window * 2 + 1
        )

        if len(dataframe) < minimum_length:

            raise ValueError(
                "Not enough candles for swing detection."
            )


    # ==================================================
    # Detect Swings
    # ==================================================

    def detect_swings(
        self,
        dataframe: pd.DataFrame,
    ) -> list[SwingPoint]:

        self._validate_data(
            dataframe
        )

        window = self.swing_window

        swings: list[SwingPoint] = []

        highs = dataframe["high"]

        lows = dataframe["low"]

        for i in range(
            window,
            len(dataframe) - window,
        ):

            current_high = float(
                highs.iloc[i]
            )

            current_low = float(
                lows.iloc[i]
            )

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
                current_high
                > left_highs.max()
                and
                current_high
                > right_highs.max()
            )

            is_swing_low = (
                current_low
                < left_lows.min()
                and
                current_low
                < right_lows.min()
            )

            index = dataframe.index[i]

            if is_swing_high:

                swings.append(
                    SwingPoint(
                        index=index,

                        price=current_high,

                        kind="H",
                    )
                )

            if is_swing_low:

                swings.append(
                    SwingPoint(
                        index=index,

                        price=current_low,

                        kind="L",
                    )
                )

        return swings


    # ==================================================
    # Classify Swings
    # ==================================================

    def classify_swings(
        self,
        swings: list[SwingPoint],
    ) -> list[SwingPoint]:

        classified: list[SwingPoint] = []

        previous_high: Optional[
            float
        ] = None

        previous_low: Optional[
            float
        ] = None

        for swing in swings:

            if swing.kind == "H":

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


    
    # ==================================================
    # Swing Classification
    # ==================================================

    def classify_swings(
        self,
        swings: list[SwingPoint],
    ) -> list[SwingPoint]:

        classified: list[SwingPoint] = []

        previous_high: float | None = None
        previous_low: float | None = None

        for swing in swings:

            # ------------------------------------------
            # Swing High
            # ------------------------------------------

            if swing.kind == "high":

                if previous_high is None:

                    label = "H"

                elif swing.price > previous_high:

                    label = "HH"

                elif swing.price < previous_high:

                    label = "LH"

                else:

                    label = "EH"

                previous_high = swing.price

            # ------------------------------------------
            # Swing Low
            # ------------------------------------------

            elif swing.kind == "low":

                if previous_low is None:

                    label = "L"

                elif swing.price > previous_low:

                    label = "HL"

                elif swing.price < previous_low:

                    label = "LL"

                else:

                    label = "EL"

            else:

                continue

            if swing.kind == "low":

                previous_low = swing.price

            classified.append(
                SwingPoint(
                    index=swing.index,
                    price=float(swing.price),
                    kind=label,
                )
            )

        return classified


    # ==================================================
    # Trend Detection
    # ==================================================

    def detect_trend(
        self,
        classified_swings: list[SwingPoint],
    ) -> str:

        if not classified_swings:
            return "range"

        bullish_score = 0
        bearish_score = 0

        for swing in classified_swings:

            if swing.kind in (
                "HH",
                "HL",
            ):

                bullish_score += 1

            elif swing.kind in (
                "LH",
                "LL",
            ):

                bearish_score += 1

        if bullish_score > bearish_score:

            return "bullish"

        if bearish_score > bullish_score:

            return "bearish"

        return "range"


    # ==================================================
    # Latest Swing Helpers
    # ==================================================

    @staticmethod
    def _latest_swing_high(
        swings: list[SwingPoint],
    ) -> SwingPoint | None:

        highs = [
            swing
            for swing in swings
            if swing.kind in (
                "H",
                "HH",
                "LH",
            )
        ]

        if not highs:
            return None

        return highs[-1]


    @staticmethod
    def _latest_swing_low(
        swings: list[SwingPoint],
    ) -> SwingPoint | None:

        lows = [
            swing
            for swing in swings
            if swing.kind in (
                "L",
                "HL",
                "LL",
            )
        ]

        if not lows:
            return None

        return lows[-1]


    # ==================================================
    # Structure Event Detection
    # ==================================================

    def detect_structure_events(
        self,
        dataframe: pd.DataFrame,
        classified_swings: list[SwingPoint],
    ) -> list[StructureEvent]:

        if dataframe.empty:
            return []

        events: list[StructureEvent] = []

        last_swing_high: SwingPoint | None = None
        last_swing_low: SwingPoint | None = None

        previous_direction: str | None = None

        processed_bullish_break = False
        processed_bearish_break = False

        swing_by_index: dict[
            object,
            list[SwingPoint]
        ] = {}

        for swing in classified_swings:

            swing_by_index.setdefault(
                swing.index,
                []
            ).append(swing)


        # ==================================================
        # Scan Market
        # ==================================================

        for i in range(len(dataframe)):

            index = dataframe.index[i]

            close = float(
                dataframe["close"].iloc[i]
            )

            current_swings = swing_by_index.get(
                index,
                []
            )


            # ------------------------------------------
            # Update Swing High / Low
            # ------------------------------------------

            for swing in current_swings:

                if swing.kind in (
                    "H",
                    "HH",
                    "LH",
                ):

                    last_swing_high = swing

                    processed_bullish_break = False


                elif swing.kind in (
                    "L",
                    "HL",
                    "LL",
                ):

                    last_swing_low = swing

                    processed_bearish_break = False


            # ------------------------------------------
            # Bullish Break
            # ------------------------------------------

            bullish_break = (

                last_swing_high is not None

                and

                close > last_swing_high.price

                and

                not processed_bullish_break

            )


            # ------------------------------------------
            # Bearish Break
            # ------------------------------------------

            bearish_break = (

                last_swing_low is not None

                and

                close < last_swing_low.price

                and

                not processed_bearish_break

            )


            # ------------------------------------------
            # Bullish Event
            # ------------------------------------------

            if bullish_break:

                event_type = (

                    "BOS"

                    if previous_direction in (
                        None,
                        "bullish",
                    )

                    else

                    "CHoCH"

                )

                events.append(
                    StructureEvent(
                        event=event_type,
                        index=index,
                        price=close,
                        direction="bullish",
                    )
                )

                previous_direction = "bullish"

                processed_bullish_break = True


            # ------------------------------------------
            # Bearish Event
            # ------------------------------------------

            elif bearish_break:

                event_type = (

                    "BOS"

                    if previous_direction in (
                        None,
                        "bearish",
                    )

                    else

                    "CHoCH"

                )

                events.append(
                    StructureEvent(
                        event=event_type,
                        index=index,
                        price=close,
                        direction="bearish",
                    )
                )

                previous_direction = "bearish"

                processed_bearish_break = True


        return events


    
    # ==================================================
    # Structure Summary
    # ==================================================

    @staticmethod
    def summarize_events(
        events: list[StructureEvent],
    ) -> dict[str, Any]:

        bos_events = [
            event
            for event in events
            if event.event == "BOS"
        ]

        choch_events = [
            event
            for event in events
            if event.event == "CHoCH"
        ]

        bullish_events = [
            event
            for event in events
            if event.direction == "bullish"
        ]

        bearish_events = [
            event
            for event in events
            if event.direction == "bearish"
        ]

        latest_event = (
            events[-1]
            if events
            else None
        )

        return {
            "bos_count": len(bos_events),
            "choch_count": len(choch_events),
            "bullish_count": len(bullish_events),
            "bearish_count": len(bearish_events),
            "latest_event": (
                latest_event.event
                if latest_event
                else None
            ),
            "latest_direction": (
                latest_event.direction
                if latest_event
                else None
            ),
            "latest_price": (
                latest_event.price
                if latest_event
                else None
            ),
        }


    # ==================================================
    # Structure Score
    # ==================================================

    @staticmethod
    def calculate_structure_score(
        trend: str,
        events: list[StructureEvent],
    ) -> float:

        score = 50.0

        if trend == "bullish":
            score += 15.0

        elif trend == "bearish":
            score -= 15.0

        for event in events[-5:]:

            if event.event == "BOS":

                if event.direction == "bullish":
                    score += 7.0

                elif event.direction == "bearish":
                    score -= 7.0

            elif event.event == "CHoCH":

                if event.direction == "bullish":
                    score += 10.0

                elif event.direction == "bearish":
                    score -= 10.0

        return round(
            max(
                0.0,
                min(
                    100.0,
                    score
                )
            ),
            2
        )


    # ==================================================
    # Latest Structure State
    # ==================================================

    @staticmethod
    def latest_structure(
        events: list[StructureEvent],
    ) -> str:

        if not events:
            return "NONE"

        latest = events[-1]

        return (
            f"{latest.event}_{latest.direction.upper()}"
        )


    # ==================================================
    # Main Analysis
    # ==================================================

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        self._validate_data(
            dataframe
        )

        # ------------------------------------------
        # Detect Swings
        # ------------------------------------------

        swings = self.detect_swings(
            dataframe
        )

        # ------------------------------------------
        # Classify Swings
        # ------------------------------------------

        classified = self.classify_swings(
            swings
        )

        # ------------------------------------------
        # Detect Trend
        # ------------------------------------------

        trend = self.detect_trend(
            classified
        )

        # ------------------------------------------
        # Detect BOS / CHoCH
        # ------------------------------------------

        events = self.detect_structure_events(
            dataframe,
            classified,
        )

        # ------------------------------------------
        # Structure Summary
        # ------------------------------------------

        event_summary = (
            self.summarize_events(
                events
            )
        )

        # ------------------------------------------
        # Structure Score
        # ------------------------------------------

        structure_score = (
            self.calculate_structure_score(
                trend=trend,
                events=events,
            )
        )

        # ------------------------------------------
        # Latest Structure
        # ------------------------------------------

        latest_structure = (
            self.latest_structure(
                events
            )
        )

        # ------------------------------------------
        # Latest Swing High / Low
        # ------------------------------------------

        latest_high = (
            self._latest_swing_high(
                classified
            )
        )

        latest_low = (
            self._latest_swing_low(
                classified
            )
        )

        # ------------------------------------------
        # Final Output
        # ------------------------------------------

        return {

            "trend": trend,

            "structure": latest_structure,

            "structure_score": structure_score,

            "swings": classified,

            "events": events,

            "event_summary": event_summary,

            "latest_swing_high": (
                latest_high.price
                if latest_high
                else None
            ),

            "latest_swing_low": (
                latest_low.price
                if latest_low
                else None
            ),

            "latest_swing_high_type": (
                latest_high.kind
                if latest_high
                else None
            ),

            "latest_swing_low_type": (
                latest_low.kind
                if latest_low
                else None
            ),
        }


# ==================================================
# Backward-Compatible Alias
# ==================================================

MarketStructureDetector = MarketStructureAnalyzer
