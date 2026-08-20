from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import math
import pandas as pd


@dataclass(frozen=True)
class TimeCycle:
    start_index: Any
    end_index: Any
    bars: int
    cycle_type: str
    strength: float


@dataclass(frozen=True)
class TimeProjection:
    source_index: Any
    target_index: Any
    bars: int
    ratio: float


class TimeAnalysis:
    """
    Time-based market analysis engine.

    Detects:
    - Distance between swing points
    - Repeating time cycles
    - Fibonacci time projections
    - Time symmetry between market legs

    This module analyzes temporal relationships.
    It does not produce standalone trade signals.
    """

    FIBONACCI_RATIOS = (
        0.382,
        0.500,
        0.618,
        0.786,
        1.000,
        1.272,
        1.414,
        1.618,
        2.000,
        2.618,
    )

    def __init__(
        self,
        swing_window: int = 2,
        tolerance: float = 0.15,
    ) -> None:

        if swing_window < 1:
            raise ValueError(
                "swing_window must be >= 1."
            )

        if tolerance <= 0:
            raise ValueError(
                "tolerance must be > 0."
            )

        self.swing_window = swing_window
        self.tolerance = tolerance

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

    def _find_swing_indices(
        self,
        dataframe: pd.DataFrame,
    ) -> list[int]:

        highs = dataframe["high"]
        lows = dataframe["low"]

        window = self.swing_window
        indices: list[int] = []

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
                >= float(left_highs.max())
                and
                current_high
                >= float(right_highs.max())
            )

            is_swing_low = (
                current_low
                <= float(left_lows.min())
                and
                current_low
                <= float(right_lows.min())
            )

            if is_swing_high or is_swing_low:
                indices.append(i)

        return indices

    def calculate_swing_durations(
        self,
        dataframe: pd.DataFrame,
    ) -> list[int]:

        self._validate(dataframe)

        swing_indices = (
            self._find_swing_indices(
                dataframe
            )
        )

        if len(swing_indices) < 2:
            return []

        return [
            swing_indices[i]
            - swing_indices[i - 1]
            for i in range(
                1,
                len(swing_indices),
            )
        ]

    def detect_cycles(
        self,
        dataframe: pd.DataFrame,
    ) -> list[TimeCycle]:

        self._validate(dataframe)

        swing_indices = (
            self._find_swing_indices(
                dataframe
            )
        )

        if len(swing_indices) < 2:
            return []

        durations = [
            swing_indices[i]
            - swing_indices[i - 1]
            for i in range(
                1,
                len(swing_indices),
            )
        ]

        cycles: list[TimeCycle] = []

        for i, bars in enumerate(
            durations,
            start=1,
        ):

            if bars <= 0:
                continue

            strength = 0.5

            if len(durations) >= 3:

                nearby = durations[
                    max(0, i - 3):i
                ]

                average = (
                    sum(nearby)
                    / len(nearby)
                )

                deviation = abs(
                    bars - average
                )

                strength = max(
                    0.0,
                    min(
                        1.0,
                        1.0
                        - (
                            deviation
                            / max(
                                average,
                                1.0,
                            )
                        ),
                    ),
                )

            cycles.append(
                TimeCycle(
                    start_index=dataframe.index[
                        swing_indices[i - 1]
                    ],
                    end_index=dataframe.index[
                        swing_indices[i]
                    ],
                    bars=bars,
                    cycle_type="swing_cycle",
                    strength=strength,
                )
            )

        return cycles

    def fibonacci_time_projections(
        self,
        dataframe: pd.DataFrame,
    ) -> list[TimeProjection]:

        self._validate(dataframe)

        swing_indices = (
            self._find_swing_indices(
                dataframe
            )
        )

        if len(swing_indices) < 3:
            return []

        projections: list[
            TimeProjection
        ] = []

        for i in range(
            1,
            len(swing_indices) - 1,
        ):

            first = swing_indices[i - 1]
            second = swing_indices[i]

            base_bars = second - first

            if base_bars <= 0:
                continue

            source_index = (
                dataframe.index[second]
            )

            for ratio in (
                self.FIBONACCI_RATIOS
            ):

                projected_bars = max(
                    1,
                    round(
                        base_bars * ratio
                    ),
                )

                target_position = (
                    second
                    + projected_bars
                )

                if (
                    target_position
                    >= len(dataframe)
                ):
                    continue

                projections.append(
                    TimeProjection(
                        source_index=source_index,
                        target_index=dataframe.index[
                            target_position
                        ],
                        bars=projected_bars,
                        ratio=ratio,
                    )
                )

        return projections

    def detect_time_symmetry(
        self,
        dataframe: pd.DataFrame,
    ) -> list[dict[str, Any]]:

        self._validate(dataframe)

        swing_indices = (
            self._find_swing_indices(
                dataframe
            )
        )

        if len(swing_indices) < 4:
            return []

        results: list[
            dict[str, Any]
        ] = []

        for i in range(
            2,
            len(swing_indices),
        ):

            first_leg = (
                swing_indices[i - 1]
                - swing_indices[i - 2]
            )

            second_leg = (
                swing_indices[i]
                - swing_indices[i - 1]
            )

            if first_leg <= 0:
                continue

            ratio = (
                second_leg
                / first_leg
            )

            symmetry_error = abs(
                ratio - 1.0
            )

            strength = max(
                0.0,
                min(
                    1.0,
                    1.0
                    - symmetry_error,
                ),
            )

            results.append(
                {
                    "index": dataframe.index[
                        swing_indices[i]
                    ],
                    "first_leg_bars": first_leg,
                    "second_leg_bars": second_leg,
                    "ratio": ratio,
                    "symmetry_strength": strength,
                }
            )

        return results

    def dominant_cycle(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any] | None:

        cycles = self.detect_cycles(
            dataframe
        )

        if not cycles:
            return None

        durations = [
            cycle.bars
            for cycle in cycles
        ]

        frequency: dict[int, int] = {}

        for duration in durations:
            frequency[duration] = (
                frequency.get(
                    duration,
                    0,
                )
                + 1
            )

        dominant_bars = max(
            frequency,
            key=frequency.get,
        )

        occurrences = frequency[
            dominant_bars
        ]

        return {
            "bars": dominant_bars,
            "occurrences": occurrences,
            "strength": min(
                1.0,
                occurrences
                / len(durations),
            ),
        }

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        self._validate(dataframe)

        cycles = self.detect_cycles(
            dataframe
        )

        projections = (
            self.fibonacci_time_projections(
                dataframe
            )
        )

        symmetry = (
            self.detect_time_symmetry(
                dataframe
            )
        )

        dominant = (
            self.dominant_cycle(
                dataframe
            )
        )

        average_cycle = None

        if cycles:
            average_cycle = (
                sum(
                    cycle.bars
                    for cycle in cycles
                )
                / len(cycles)
            )

        return {
            "cycles": cycles,
            "average_cycle_bars": (
                average_cycle
            ),
            "dominant_cycle": dominant,
            "fibonacci_projections": (
                projections
            ),
            "time_symmetry": symmetry,
        }
