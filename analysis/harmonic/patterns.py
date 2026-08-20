from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from analysis.market_structure import (
    MarketStructureAnalyzer,
    SwingPoint,
)


@dataclass(frozen=True)
class HarmonicPattern:
    name: str
    direction: str
    points: tuple[SwingPoint, ...]
    score: float
    ratios: dict[str, float]


class HarmonicAnalyzer:
    """
    Harmonic pattern detection engine.

    Supported patterns:
    - Gartley
    - Bat
    - Butterfly
    - Crab
    - AB=CD

    Pattern detection is probabilistic and based on
    Fibonacci ratio tolerances.
    """

    def __init__(
        self,
        swing_window: int = 2,
        tolerance: float = 0.10,
    ) -> None:

        if swing_window < 1:
            raise ValueError(
                "swing_window must be >= 1."
            )

        if tolerance <= 0:
            raise ValueError(
                "tolerance must be > 0."
            )

        self.structure = (
            MarketStructureAnalyzer(
                swing_window=swing_window
            )
        )

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

    @staticmethod
    def _distance(
        first: float,
        second: float,
    ) -> float:

        return abs(first - second)

    def _ratio(
        self,
        numerator: float,
        denominator: float,
    ) -> float:

        if abs(denominator) < 1e-12:
            return 0.0

        return abs(numerator / denominator)

    def _matches(
        self,
        value: float,
        target: float,
    ) -> bool:

        return abs(
            value - target
        ) <= self.tolerance

    def _score_ratios(
        self,
        ratios: dict[str, float],
        targets: dict[str, float],
    ) -> float:

        if not targets:
            return 0.0

        score = 0.0

        for key, target in targets.items():

            value = ratios.get(key)

            if value is None:
                continue

            error = abs(
                value - target
            )

            normalized = max(
                0.0,
                1.0
                - (
                    error
                    / max(
                        self.tolerance,
                        1e-12,
                    )
                ),
            )

            score += normalized

        return (
            score
            / len(targets)
            * 100
        )

    def _alternating_swings(
        self,
        dataframe: pd.DataFrame,
    ) -> list[SwingPoint]:

        swings = (
            self.structure.detect_swings(
                dataframe
            )
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

                if swing.kind == "high":

                    if (
                        swing.price
                        > previous.price
                    ):
                        result[-1] = swing

                else:

                    if (
                        swing.price
                        < previous.price
                    ):
                        result[-1] = swing

            else:
                result.append(swing)

        return result

    def _calculate_ratios(
        self,
        x: SwingPoint,
        a: SwingPoint,
        b: SwingPoint,
        c: SwingPoint,
        d: SwingPoint,
    ) -> dict[str, float]:

        xa = self._distance(
            x.price,
            a.price,
        )

        ab = self._distance(
            a.price,
            b.price,
        )

        bc = self._distance(
            b.price,
            c.price,
        )

        cd = self._distance(
            c.price,
            d.price,
        )

        return {
            "AB_XA": self._ratio(
                ab,
                xa,
            ),
            "BC_AB": self._ratio(
                bc,
                ab,
            ),
            "CD_BC": self._ratio(
                cd,
                bc,
            ),
            "AD_XA": self._ratio(
                self._distance(
                    a.price,
                    d.price,
                ),
                xa,
            ),
        }

    def _detect_gartley(
        self,
        points: tuple[SwingPoint, ...],
    ) -> HarmonicPattern | None:

        x, a, b, c, d = points

        ratios = self._calculate_ratios(
            x,
            a,
            b,
            c,
            d,
        )

        targets = {
            "AB_XA": 0.618,
            "BC_AB": 0.618,
            "CD_BC": 1.618,
            "AD_XA": 0.786,
        }

        score = self._score_ratios(
            ratios,
            targets,
        )

        if score < 60:
            return None

        direction = (
            "bullish"
            if d.price < c.price
            else "bearish"
        )

        return HarmonicPattern(
            name="gartley",
            direction=direction,
            points=points,
            score=score,
            ratios=ratios,
        )

    def _detect_bat(
        self,
        points: tuple[SwingPoint, ...],
    ) -> HarmonicPattern | None:

        x, a, b, c, d = points

        ratios = self._calculate_ratios(
            x,
            a,
            b,
            c,
            d,
        )

        targets = {
            "AB_XA": 0.382,
            "BC_AB": 0.618,
            "CD_BC": 2.0,
            "AD_XA": 0.886,
        }

        score = self._score_ratios(
            ratios,
            targets,
        )

        if score < 60:
            return None

        direction = (
            "bullish"
            if d.price < c.price
            else "bearish"
        )

        return HarmonicPattern(
            name="bat",
            direction=direction,
            points=points,
            score=score,
            ratios=ratios,
        )

    def _detect_butterfly(
        self,
        points: tuple[SwingPoint, ...],
    ) -> HarmonicPattern | None:

        x, a, b, c, d = points

        ratios = self._calculate_ratios(
            x,
            a,
            b,
            c,
            d,
        )

        targets = {
            "AB_XA": 0.786,
            "BC_AB": 0.618,
            "CD_BC": 1.618,
            "AD_XA": 1.27,
        }

        score = self._score_ratios(
            ratios,
            targets,
        )

        if score < 60:
            return None

        direction = (
            "bullish"
            if d.price < c.price
            else "bearish"
        )

        return HarmonicPattern(
            name="butterfly",
            direction=direction,
            points=points,
            score=score,
            ratios=ratios,
        )

    def _detect_crab(
        self,
        points: tuple[SwingPoint, ...],
    ) -> HarmonicPattern | None:

        x, a, b, c, d = points

        ratios = self._calculate_ratios(
            x,
            a,
            b,
            c,
            d,
        )

        targets = {
            "AB_XA": 0.382,
            "BC_AB": 0.618,
            "CD_BC": 2.618,
            "AD_XA": 1.618,
        }

        score = self._score_ratios(
            ratios,
            targets,
        )

        if score < 60:
            return None

        direction = (
            "bullish"
            if d.price < c.price
            else "bearish"
        )

        return HarmonicPattern(
            name="crab",
            direction=direction,
            points=points,
            score=score,
            ratios=ratios,
        )

    def _detect_abcd(
        self,
        points: tuple[SwingPoint, ...],
    ) -> HarmonicPattern | None:

        a, b, c, d = points[-4:]

        ab = self._distance(
            a.price,
            b.price,
        )

        cd = self._distance(
            c.price,
            d.price,
        )

        if ab <= 1e-12:
            return None

        ratio = cd / ab

        score = max(
            0.0,
            100.0
            - abs(
                ratio - 1.0
            )
            / max(
                self.tolerance,
                1e-12,
            )
            * 100.0,
        )

        if score < 60:
            return None

        direction = (
            "bullish"
            if d.price < c.price
            else "bearish"
        )

        return HarmonicPattern(
            name="abcd",
            direction=direction,
            points=points[-4:],
            score=min(
                score,
                100.0,
            ),
            ratios={
                "CD_AB": ratio,
            },
        )

    def detect_patterns(
        self,
        dataframe: pd.DataFrame,
    ) -> list[HarmonicPattern]:

        self._validate(dataframe)

        swings = (
            self._alternating_swings(
                dataframe
            )
        )

        patterns: list[
            HarmonicPattern
        ] = []

        if len(swings) >= 5:

            for i in range(
                len(swings) - 4
            ):

                points = tuple(
                    swings[
                        i:i + 5
                    ]
                )

                detectors = (
                    self._detect_gartley,
                    self._detect_bat,
                    self._detect_butterfly,
                    self._detect_crab,
                )

                for detector in detectors:

                    pattern = detector(
                        points
                    )

                    if pattern is not None:
                        patterns.append(
                            pattern
                        )

        if len(swings) >= 4:

            for i in range(
                len(swings) - 3
            ):

                points = tuple(
                    swings[
                        i:i + 4
                    ]
                )

                pattern = (
                    self._detect_abcd(
                        points
                    )
                )

                if pattern is not None:
                    patterns.append(
                        pattern
                    )

        patterns.sort(
            key=lambda pattern:
                pattern.score,
            reverse=True,
        )

        return patterns

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        patterns = (
            self.detect_patterns(
                dataframe
            )
        )

        bullish = [
            pattern
            for pattern in patterns
            if pattern.direction
            == "bullish"
        ]

        bearish = [
            pattern
            for pattern in patterns
            if pattern.direction
            == "bearish"
        ]

        bullish_score = sum(
            pattern.score
            for pattern in bullish[:5]
        )

        bearish_score = sum(
            pattern.score
            for pattern in bearish[:5]
        )

        if bullish_score > bearish_score:
            bias = "bullish"

        elif bearish_score > bullish_score:
            bias = "bearish"

        else:
            bias = "neutral"

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
            "patterns": patterns,
            "best_pattern": (
                patterns[0]
                if patterns
                else None
            ),
        }
