from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from analysis.market_structure import (
    MarketStructureAnalyzer,
    SwingPoint,
)


@dataclass(frozen=True)
class WavePoint:
    index: Any
    price: float
    label: str


@dataclass(frozen=True)
class ElliottScenario:
    direction: str
    structure: str
    points: tuple[WavePoint, ...]
    score: float
    notes: tuple[str, ...]


class ElliottWaveAnalyzer:
    """
    Scenario-based Elliott Wave analyzer.

    This module does not claim that a wave count is certain.
    It generates candidate structures from market swings and
    assigns a heuristic score.

    Supported initial concepts:
    - Impulsive 5-wave candidate
    - Corrective 3-wave candidate
    - Basic alternation checks
    - Basic Fibonacci relationships
    - Scenario scoring
    """

    def __init__(
        self,
        swing_window: int = 2,
    ) -> None:

        self.structure = (
            MarketStructureAnalyzer(
                swing_window=swing_window
            )
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
    def _ratio(
        numerator: float,
        denominator: float,
    ) -> float:

        if abs(denominator) < 1e-12:
            return 0.0

        return abs(numerator / denominator)

    @staticmethod
    def _near(
        value: float,
        target: float,
        tolerance: float = 0.15,
    ) -> bool:

        return abs(value - target) <= tolerance

    def _extract_alternating_swings(
        self,
        dataframe: pd.DataFrame,
    ) -> list[SwingPoint]:

        swings = self.structure.detect_swings(
            dataframe
        )

        if not swings:
            return []

        result: list[SwingPoint] = []

        for swing in swings:

            if not result:
                result.append(swing)
                continue

            previous = result[-1]

            if swing.kind == previous.kind:

                # Keep the more extreme swing.
                if swing.kind == "high":
                    if swing.price > previous.price:
                        result[-1] = swing

                else:
                    if swing.price < previous.price:
                        result[-1] = swing

                continue

            result.append(swing)

        return result

    def _build_impulse_candidate(
        self,
        swings: list[SwingPoint],
    ) -> list[ElliottScenario]:

        scenarios: list[ElliottScenario] = []

        if len(swings) < 6:
            return scenarios

        for start in range(
            len(swings) - 5
        ):

            points = swings[
                start:start + 6
            ]

            first = points[0]
            second = points[1]
            third = points[2]
            fourth = points[3]
            fifth = points[4]
            sixth = points[5]

            prices = [
                point.price
                for point in points
            ]

            # --------------------------------------
            # Bullish impulse candidate
            # --------------------------------------

            bullish = (
                first.kind == "low"
                and second.kind == "high"
                and third.kind == "low"
                and fourth.kind == "high"
                and fifth.kind == "low"
                and sixth.kind == "high"
            )

            if bullish:

                wave1 = (
                    second.price
                    - first.price
                )

                wave2 = (
                    second.price
                    - third.price
                )

                wave3 = (
                    fourth.price
                    - third.price
                )

                wave4 = (
                    fourth.price
                    - fifth.price
                )

                wave5 = (
                    sixth.price
                    - fifth.price
                )

                score = 0.0
                notes = []

                # Wave 2 should not fully invalidate
                # wave 1.
                if (
                    third.price
                    > first.price
                ):
                    score += 20
                    notes.append(
                        "Wave 2 respects wave 1 origin."
                    )

                # Wave 4 should normally not overlap
                # wave 1 in a simple impulse.
                if (
                    fifth.price
                    > second.price
                ):
                    score += 15
                    notes.append(
                        "Wave 4 avoids deep overlap."
                    )

                # Wave 3 should generally not be
                # the shortest among 1, 3, 5.
                lengths = [
                    abs(wave1),
                    abs(wave3),
                    abs(wave5),
                ]

                if (
                    abs(wave3)
                    >= min(lengths)
                ):
                    score += 15

                # Fibonacci relationship.
                ratio_3_1 = self._ratio(
                    wave3,
                    wave1,
                )

                if self._near(
                    ratio_3_1,
                    1.618,
                    0.35,
                ):
                    score += 20
                    notes.append(
                        "Wave 3 has a useful Fibonacci relationship."
                    )

                # Wave 5 vs wave 1.
                ratio_5_1 = self._ratio(
                    wave5,
                    wave1,
                )

                if self._near(
                    ratio_5_1,
                    1.0,
                    0.25,
                ):
                    score += 15
                    notes.append(
                        "Wave 5 is proportionate to wave 1."
                    )

                if (
                    sixth.price
                    > fourth.price
                ):
                    score += 15
                    notes.append(
                        "Candidate completes a higher high."
                    )

                scenarios.append(
                    ElliottScenario(
                        direction="bullish",
                        structure="impulse",
                        points=tuple(
                            WavePoint(
                                index=point.index,
                                price=point.price,
                                label=str(i + 1),
                            )
                            for i, point
                            in enumerate(points)
                        ),
                        score=min(
                            score,
                            100.0,
                        ),
                        notes=tuple(notes),
                    )
                )

            # --------------------------------------
            # Bearish impulse candidate
            # --------------------------------------

            bearish = (
                first.kind == "high"
                and second.kind == "low"
                and third.kind == "high"
                and fourth.kind == "low"
                and fifth.kind == "high"
                and sixth.kind == "low"
            )

            if bearish:

                wave1 = (
                    first.price
                    - second.price
                )

                wave2 = (
                    third.price
                    - second.price
                )

                wave3 = (
                    third.price
                    - fourth.price
                )

                wave4 = (
                    fifth.price
                    - fourth.price
                )

                wave5 = (
                    fifth.price
                    - sixth.price
                )

                score = 0.0
                notes = []

                if (
                    third.price
                    < first.price
                ):
                    score += 20
                    notes.append(
                        "Wave 2 respects wave 1 origin."
                    )

                if (
                    fifth.price
                    < second.price
                ):
                    score += 15
                    notes.append(
                        "Wave 4 avoids deep overlap."
                    )

                lengths = [
                    abs(wave1),
                    abs(wave3),
                    abs(wave5),
                ]

                if (
                    abs(wave3)
                    >= min(lengths)
                ):
                    score += 15

                ratio_3_1 = self._ratio(
                    wave3,
                    wave1,
                )

                if self._near(
                    ratio_3_1,
                    1.618,
                    0.35,
                ):
                    score += 20
                    notes.append(
                        "Wave 3 has a useful Fibonacci relationship."
                    )

                ratio_5_1 = self._ratio(
                    wave5,
                    wave1,
                )

                if self._near(
                    ratio_5_1,
                    1.0,
                    0.25,
                ):
                    score += 15
                    notes.append(
                        "Wave 5 is proportionate to wave 1."
                    )

                if (
                    sixth.price
                    < fourth.price
                ):
                    score += 15
                    notes.append(
                        "Candidate completes a lower low."
                    )

                scenarios.append(
                    ElliottScenario(
                        direction="bearish",
                        structure="impulse",
                        points=tuple(
                            WavePoint(
                                index=point.index,
                                price=point.price,
                                label=str(i + 1),
                            )
                            for i, point
                            in enumerate(points)
                        ),
                        score=min(
                            score,
                            100.0,
                        ),
                        notes=tuple(notes),
                    )
                )

        return scenarios

    def _build_corrective_candidate(
        self,
        swings: list[SwingPoint],
    ) -> list[ElliottScenario]:

        scenarios: list[ElliottScenario] = []

        if len(swings) < 4:
            return scenarios

        for start in range(
            len(swings) - 3
        ):

            points = swings[
                start:start + 4
            ]

            first = points[0]
            second = points[1]
            third = points[2]
            fourth = points[3]

            # --------------------------------------
            # Bullish A-B-C candidate
            # --------------------------------------

            bullish = (
                first.kind == "high"
                and second.kind == "low"
                and third.kind == "high"
                and fourth.kind == "low"
            )

            if bullish:

                wave_a = (
                    first.price
                    - second.price
                )

                wave_b = (
                    third.price
                    - second.price
                )

                wave_c = (
                    third.price
                    - fourth.price
                )

                score = 20.0
                notes = [
                    "Alternating A-B-C swing structure detected."
                ]

                ratio_c_a = self._ratio(
                    wave_c,
                    wave_a,
                )

                if self._near(
                    ratio_c_a,
                    1.0,
                    0.30,
                ):
                    score += 30
                    notes.append(
                        "Wave C is close to wave A."
                    )

                if self._near(
                    ratio_c_a,
                    1.618,
                    0.35,
                ):
                    score += 30
                    notes.append(
                        "Wave C has a Fibonacci extension."
                    )

                if (
                    fourth.price
                    < second.price
                ):
                    score += 20

                scenarios.append(
                    ElliottScenario(
                        direction="bearish",
                        structure="corrective_ABC",
                        points=tuple(
                            WavePoint(
                                index=point.index,
                                price=point.price,
                                label=label,
                            )
                            for point, label
                            in zip(
                                points,
                                (
                                    "A",
                                    "B",
                                    "C",
                                    "END",
                                ),
                            )
                        ),
                        score=min(
                            score,
                            100.0,
                        ),
                        notes=tuple(notes),
                    )
                )

            # --------------------------------------
            # Bearish A-B-C candidate
            # --------------------------------------

            bearish = (
                first.kind == "low"
                and second.kind == "high"
                and third.kind == "low"
                and fourth.kind == "high"
            )

            if bearish:

                wave_a = (
                    second.price
                    - first.price
                )

                wave_b = (
                    second.price
                    - third.price
                )

                wave_c = (
                    fourth.price
                    - third.price
                )

                score = 20.0
                notes = [
                    "Alternating A-B-C swing structure detected."
                ]

                ratio_c_a = self._ratio(
                    wave_c,
                    wave_a,
                )

                if self._near(
                    ratio_c_a,
                    1.0,
                    0.30,
                ):
                    score += 30
                    notes.append(
                        "Wave C is close to wave A."
                    )

                if self._near(
                    ratio_c_a,
                    1.618,
                    0.35,
                ):
                    score += 30
                    notes.append(
                        "Wave C has a Fibonacci extension."
                    )

                if (
                    fourth.price
                    > second.price
                ):
                    score += 20

                scenarios.append(
                    ElliottScenario(
                        direction="bullish",
                        structure="corrective_ABC",
                        points=tuple(
                            WavePoint(
                                index=point.index,
                                price=point.price,
                                label=label,
                            )
                            for point, label
                            in zip(
                                points,
                                (
                                    "A",
                                    "B",
                                    "C",
                                    "END",
                                ),
                            )
                        ),
                        score=min(
                            score,
                            100.0,
                        ),
                        notes=tuple(notes),
                    )
                )

        return scenarios

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        self._validate(dataframe)

        swings = (
            self._extract_alternating_swings(
                dataframe
            )
        )

        impulse_scenarios = (
            self._build_impulse_candidate(
                swings
            )
        )

        corrective_scenarios = (
            self._build_corrective_candidate(
                swings
            )
        )

        scenarios = (
            impulse_scenarios
            + corrective_scenarios
        )

        scenarios.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        best = (
            scenarios[0]
            if scenarios
            else None
        )

        return {
            "best_scenario": best,
            "scenarios": scenarios,
            "swings": swings,
        }
