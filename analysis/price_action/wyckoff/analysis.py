from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class WyckoffEvent:
    index: Any
    event: str
    direction: str
    score: float
    details: dict[str, Any]


@dataclass(frozen=True)
class WyckoffPhase:
    index: Any
    phase: str
    direction: str
    score: float
    details: dict[str, Any]


class WyckoffAnalyzer:
    """
    Wyckoff-style market analysis engine.

    Detects basic Wyckoff concepts:
    - Accumulation
    - Distribution
    - Trading ranges
    - Springs
    - Upthrusts
    - Preliminary support / supply
    - Sign of strength
    - Sign of weakness
    - Breakouts
    - Volume/price relationships

    This engine provides analytical context.
    It does not generate standalone trading signals.
    """

    def __init__(
        self,
        range_period: int = 20,
        volume_period: int = 20,
        volume_multiplier: float = 1.5,
    ) -> None:

        if range_period < 5:
            raise ValueError(
                "range_period must be >= 5."
            )

        if volume_period < 2:
            raise ValueError(
                "volume_period must be >= 2."
            )

        if volume_multiplier <= 0:
            raise ValueError(
                "volume_multiplier must be > 0."
            )

        self.range_period = range_period
        self.volume_period = volume_period
        self.volume_multiplier = volume_multiplier

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

    def _volume_available(
        self,
        dataframe: pd.DataFrame,
    ) -> bool:

        return "volume" in dataframe.columns

    def _average_volume(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.Series | None:

        if not self._volume_available(
            dataframe
        ):
            return None

        return dataframe["volume"].rolling(
            self.volume_period
        ).mean()

    def _range_bounds(
        self,
        dataframe: pd.DataFrame,
        index: int,
    ) -> tuple[float, float]:

        start = max(
            0,
            index - self.range_period,
        )

        section = dataframe.iloc[
            start:index
        ]

        if section.empty:
            section = dataframe.iloc[
                max(0, index - 1):index
            ]

        return (
            float(section["high"].max()),
            float(section["low"].min()),
        )

    def detect_springs(
        self,
        dataframe: pd.DataFrame,
    ) -> list[WyckoffEvent]:

        self._validate(dataframe)

        events: list[WyckoffEvent] = []

        for i in range(
            self.range_period + 1,
            len(dataframe),
        ):

            current = dataframe.iloc[i]

            range_high, range_low = (
                self._range_bounds(
                    dataframe,
                    i,
                )
            )

            current_low = float(
                current["low"]
            )

            current_close = float(
                current["close"]
            )

            # Price briefly breaks below
            # support and closes back above it.
            spring = (
                current_low < range_low
                and current_close > range_low
            )

            if not spring:
                continue

            score = 75.0

            if self._volume_available(
                dataframe
            ):

                average_volume = (
                    self._average_volume(
                        dataframe
                    )
                )

                current_volume = float(
                    current["volume"]
                )

                avg = average_volume.iloc[i]

                if (
                    not pd.isna(avg)
                    and current_volume
                    < float(avg)
                ):
                    score += 10.0

            events.append(
                WyckoffEvent(
                    index=dataframe.index[i],
                    event="spring",
                    direction="bullish",
                    score=min(
                        score,
                        100.0,
                    ),
                    details={
                        "range_low":
                            range_low,
                        "low":
                            current_low,
                        "close":
                            current_close,
                    },
                )
            )

        return events

    def detect_upthrusts(
        self,
        dataframe: pd.DataFrame,
    ) -> list[WyckoffEvent]:

        self._validate(dataframe)

        events: list[WyckoffEvent] = []

        for i in range(
            self.range_period + 1,
            len(dataframe),
        ):

            current = dataframe.iloc[i]

            range_high, range_low = (
                self._range_bounds(
                    dataframe,
                    i,
                )
            )

            current_high = float(
                current["high"]
            )

            current_close = float(
                current["close"]
            )

            upthrust = (
                current_high > range_high
                and current_close < range_high
            )

            if not upthrust:
                continue

            score = 75.0

            if self._volume_available(
                dataframe
            ):

                average_volume = (
                    self._average_volume(
                        dataframe
                    )
                )

                current_volume = float(
                    current["volume"]
                )

                avg = average_volume.iloc[i]

                if (
                    not pd.isna(avg)
                    and current_volume
                    > float(avg)
                    * self.volume_multiplier
                ):
                    score += 10.0

            events.append(
                WyckoffEvent(
                    index=dataframe.index[i],
                    event="upthrust",
                    direction="bearish",
                    score=min(
                        score,
                        100.0,
                    ),
                    details={
                        "range_high":
                            range_high,
                        "high":
                            current_high,
                        "close":
                            current_close,
                    },
                )
            )

        return events

    def detect_sign_of_strength(
        self,
        dataframe: pd.DataFrame,
    ) -> list[WyckoffEvent]:

        self._validate(dataframe)

        events: list[WyckoffEvent] = []

        for i in range(
            self.range_period,
            len(dataframe),
        ):

            current = dataframe.iloc[i]

            range_high, _ = (
                self._range_bounds(
                    dataframe,
                    i,
                )
            )

            close = float(
                current["close"]
            )

            candle_range = (
                float(current["high"])
                - float(current["low"])
            )

            if candle_range <= 0:
                continue

            close_position = (
                close - float(current["low"])
            ) / candle_range

            strong_close = (
                close_position >= 0.75
            )

            breakout = (
                close > range_high
            )

            if strong_close and breakout:

                score = 80.0

                if self._volume_available(
                    dataframe
                ):

                    average_volume = (
                        self._average_volume(
                            dataframe
                        )
                    )

                    avg = average_volume.iloc[i]

                    if (
                        not pd.isna(avg)
                        and float(
                            current["volume"]
                        )
                        > float(avg)
                        * self.volume_multiplier
                    ):
                        score += 10.0

                events.append(
                    WyckoffEvent(
                        index=dataframe.index[i],
                        event="sign_of_strength",
                        direction="bullish",
                        score=min(
                            score,
                            100.0,
                        ),
                        details={
                            "range_high":
                                range_high,
                            "close":
                                close,
                            "close_position":
                                close_position,
                        },
                    )
                )

        return events

    def detect_sign_of_weakness(
        self,
        dataframe: pd.DataFrame,
    ) -> list[WyckoffEvent]:

        self._validate(dataframe)

        events: list[WyckoffEvent] = []

        for i in range(
            self.range_period,
            len(dataframe),
        ):

            current = dataframe.iloc[i]

            _, range_low = (
                self._range_bounds(
                    dataframe,
                    i,
                )
            )

            close = float(
                current["close"]
            )

            candle_range = (
                float(current["high"])
                - float(current["low"])
            )

            if candle_range <= 0:
                continue

            close_position = (
                close - float(current["low"])
            ) / candle_range

            weak_close = (
                close_position <= 0.25
            )

            breakdown = (
                close < range_low
            )

            if weak_close and breakdown:

                score = 80.0

                if self._volume_available(
                    dataframe
                ):

                    average_volume = (
                        self._average_volume(
                            dataframe
                        )
                    )

                    avg = average_volume.iloc[i]

                    if (
                        not pd.isna(avg)
                        and float(
                            current["volume"]
                        )
                        > float(avg)
                        * self.volume_multiplier
                    ):
                        score += 10.0

                events.append(
                    WyckoffEvent(
                        index=dataframe.index[i],
                        event="sign_of_weakness",
                        direction="bearish",
                        score=min(
                            score,
                            100.0,
                        ),
                        details={
                            "range_low":
                                range_low,
                            "close":
                                close,
                            "close_position":
                                close_position,
                        },
                    )
                )

        return events

    def detect_volume_climax(
        self,
        dataframe: pd.DataFrame,
    ) -> list[WyckoffEvent]:

        self._validate(dataframe)

        if not self._volume_available(
            dataframe
        ):
            return []

        average_volume = (
            self._average_volume(
                dataframe
            )
        )

        events: list[WyckoffEvent] = []

        for i in range(
            self.volume_period,
            len(dataframe),
        ):

            current = dataframe.iloc[i]

            avg = average_volume.iloc[i]

            if pd.isna(avg):
                continue

            volume = float(
                current["volume"]
            )

            if (
                volume
                < float(avg)
                * self.volume_multiplier
            ):
                continue

            candle_range = (
                float(current["high"])
                - float(current["low"])
            )

            if candle_range <= 0:
                continue

            body = abs(
                float(current["close"])
                - float(current["open"])
            )

            body_ratio = (
                body / candle_range
            )

            if body_ratio >= 0.70:

                direction = (
                    "bullish"
                    if float(
                        current["close"]
                    )
                    > float(current["open"])
                    else "bearish"
                )

                event = (
                    "buying_climax"
                    if direction
                    == "bullish"
                    else "selling_climax"
                )

                events.append(
                    WyckoffEvent(
                        index=dataframe.index[i],
                        event=event,
                        direction=direction,
                        score=78.0,
                        details={
                            "volume":
                                volume,
                            "average_volume":
                                float(avg),
                            "volume_ratio":
                                volume
                                / float(avg),
                        },
                    )
                )

        return events

    def detect_phase(
        self,
        dataframe: pd.DataFrame,
    ) -> list[WyckoffPhase]:

        self._validate(dataframe)

        phases: list[WyckoffPhase] = []

        for i in range(
            self.range_period,
            len(dataframe),
        ):

            range_high, range_low = (
                self._range_bounds(
                    dataframe,
                    i,
                )
            )

            current_close = float(
                dataframe["close"].iloc[i]
            )

            width = (
                range_high - range_low
            )

            if width <= 0:
                continue

            position = (
                current_close - range_low
            ) / width

            recent_close = float(
                dataframe["close"].iloc[
                    i - 5:i + 1
                ].mean()
            )

            previous_close = float(
                dataframe["close"].iloc[
                    max(0, i - 10):i - 5
                ].mean()
            )

            if (
                0.20 <= position <= 0.80
                and recent_close
                > previous_close
            ):

                phase = "accumulation_candidate"
                direction = "bullish"
                score = 65.0

            elif (
                0.20 <= position <= 0.80
                and recent_close
                < previous_close
            ):

                phase = "distribution_candidate"
                direction = "bearish"
                score = 65.0

            elif position > 0.80:

                phase = "upper_range"
                direction = "bullish"
                score = 50.0

            elif position < 0.20:

                phase = "lower_range"
                direction = "bearish"
                score = 50.0

            else:

                phase = "neutral_range"
                direction = "neutral"
                score = 40.0

            phases.append(
                WyckoffPhase(
                    index=dataframe.index[i],
                    phase=phase,
                    direction=direction,
                    score=score,
                    details={
                        "range_high":
                            range_high,
                        "range_low":
                            range_low,
                        "position":
                            position,
                    },
                )
            )

        return phases

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        self._validate(dataframe)

        springs = self.detect_springs(
            dataframe
        )

        upthrusts = (
            self.detect_upthrusts(
                dataframe
            )
        )

        strength = (
            self.detect_sign_of_strength(
                dataframe
            )
        )

        weakness = (
            self.detect_sign_of_weakness(
                dataframe
            )
        )

        climaxes = (
            self.detect_volume_climax(
                dataframe
            )
        )

        phases = self.detect_phase(
            dataframe
        )

        events = (
            springs
            + upthrusts
            + strength
            + weakness
            + climaxes
        )

        bullish_score = sum(
            event.score
            for event in events
            if event.direction
            == "bullish"
        )

        bearish_score = sum(
            event.score
            for event in events
            if event.direction
            == "bearish"
        )

        if bullish_score > bearish_score:
            bias = "bullish"

        elif bearish_score > bullish_score:
            bias = "bearish"

        else:
            bias = "neutral"

        current_phase = (
            phases[-1]
            if phases
            else None
        )

        return {
            "bias": bias,
            "bullish_score": round(
                bullish_score,
                2,
            ),
            "bearish_score": round(
                bearish_score,
                2,
            ),
            "current_phase":
                current_phase,
            "phases": phases,
            "springs": springs,
            "upthrusts": upthrusts,
            "sign_of_strength":
                strength,
            "sign_of_weakness":
                weakness,
            "volume_climaxes":
                climaxes,
            "events": events,
        }
