from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AnalysisResult:
    """
    Standardized result produced by one analysis engine.
    """

    name: str
    direction: str
    score: float
    confidence: float = 1.0
    weight: float = 1.0
    timeframe: str | None = None
    details: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class ConfluenceResult:
    """
    Combined result of multiple analysis engines.
    """

    direction: str
    bullish_score: float
    bearish_score: float
    neutral_score: float
    confidence: float
    agreement: float
    participating_engines: int
    results: list[AnalysisResult]
    reasons: list[str]


class ConfluenceEngine:
    """
    Combines independent analysis engines into
    one standardized market-context assessment.

    This engine does NOT place trades and does NOT
    produce broker orders.
    """

    VALID_DIRECTIONS = {
        "bullish",
        "bearish",
        "neutral",
    }

    def __init__(
        self,
        minimum_confidence: float = 0.0,
    ) -> None:

        if not 0 <= minimum_confidence <= 1:
            raise ValueError(
                "minimum_confidence must be between 0 and 1."
            )

        self.minimum_confidence = (
            minimum_confidence
        )

    def _validate_result(
        self,
        result: AnalysisResult,
    ) -> None:

        if result.direction not in (
            self.VALID_DIRECTIONS
        ):
            raise ValueError(
                f"Invalid direction: "
                f"{result.direction}"
            )

        if not 0 <= result.score <= 100:
            raise ValueError(
                f"Score must be between 0 and 100: "
                f"{result.score}"
            )

        if not 0 <= result.confidence <= 1:
            raise ValueError(
                f"Confidence must be between 0 and 1: "
                f"{result.confidence}"
            )

        if result.weight < 0:
            raise ValueError(
                "Weight cannot be negative."
            )

    def add_result(
        self,
        results: list[AnalysisResult],
        *,
        name: str,
        direction: str,
        score: float,
        confidence: float = 1.0,
        weight: float = 1.0,
        timeframe: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:

        result = AnalysisResult(
            name=name,
            direction=direction,
            score=score,
            confidence=confidence,
            weight=weight,
            timeframe=timeframe,
            details=details or {},
        )

        self._validate_result(result)

        if (
            result.confidence
            >= self.minimum_confidence
        ):
            results.append(result)

    def _weighted_score(
        self,
        results: list[AnalysisResult],
        direction: str,
    ) -> float:

        numerator = 0.0
        denominator = 0.0

        for result in results:

            if result.direction != direction:
                continue

            effective_weight = (
                result.weight
                * result.confidence
            )

            numerator += (
                result.score
                * effective_weight
            )

            denominator += (
                effective_weight
            )

        if denominator <= 0:
            return 0.0

        return numerator / denominator

    def _agreement(
        self,
        results: list[AnalysisResult],
    ) -> float:

        if not results:
            return 0.0

        bullish = sum(
            1
            for result in results
            if result.direction
            == "bullish"
        )

        bearish = sum(
            1
            for result in results
            if result.direction
            == "bearish"
        )

        neutral = sum(
            1
            for result in results
            if result.direction
            == "neutral"
        )

        total = (
            bullish
            + bearish
            + neutral
        )

        if total == 0:
            return 0.0

        dominant = max(
            bullish,
            bearish,
            neutral,
        )

        return dominant / total

    def _confidence(
        self,
        results: list[AnalysisResult],
        agreement: float,
    ) -> float:

        if not results:
            return 0.0

        total_weight = sum(
            result.weight
            for result in results
        )

        if total_weight <= 0:
            return 0.0

        weighted_confidence = sum(
            result.confidence
            * result.weight
            for result in results
        ) / total_weight

        score_confidence = min(
            1.0,
            agreement
            * 0.7
            + weighted_confidence
            * 0.3,
        )

        return score_confidence

    def _reasons(
        self,
        results: list[AnalysisResult],
        direction: str,
    ) -> list[str]:

        reasons: list[str] = []

        for result in results:

            if result.direction != direction:
                continue

            reason = (
                f"{result.name}: "
                f"{result.direction} "
                f"(score={result.score:.1f}, "
                f"confidence="
                f"{result.confidence:.2f})"
            )

            if result.timeframe:
                reason += (
                    f", timeframe="
                    f"{result.timeframe}"
                )

            reasons.append(reason)

        return reasons

    def combine(
        self,
        results: list[AnalysisResult],
    ) -> ConfluenceResult:

        for result in results:
            self._validate_result(result)

        if not results:

            return ConfluenceResult(
                direction="neutral",
                bullish_score=0.0,
                bearish_score=0.0,
                neutral_score=0.0,
                confidence=0.0,
                agreement=0.0,
                participating_engines=0,
                results=[],
                reasons=[],
            )

        bullish_score = (
            self._weighted_score(
                results,
                "bullish",
            )
        )

        bearish_score = (
            self._weighted_score(
                results,
                "bearish",
            )
        )

        neutral_score = (
            self._weighted_score(
                results,
                "neutral",
            )
        )

        scores = {
            "bullish": bullish_score,
            "bearish": bearish_score,
            "neutral": neutral_score,
        }

        direction = max(
            scores,
            key=scores.get,
        )

        agreement = self._agreement(
            results
        )

        confidence = self._confidence(
            results,
            agreement,
        )

        reasons = self._reasons(
            results,
            direction,
        )

        return ConfluenceResult(
            direction=direction,
            bullish_score=round(
                bullish_score,
                2,
            ),
            bearish_score=round(
                bearish_score,
                2,
            ),
            neutral_score=round(
                neutral_score,
                2,
            ),
            confidence=round(
                confidence,
                4,
            ),
            agreement=round(
                agreement,
                4,
            ),
            participating_engines=len(
                results
            ),
            results=list(results),
            reasons=reasons,
        )

    def summarize(
        self,
        result: ConfluenceResult,
    ) -> dict[str, Any]:

        return {
            "direction":
                result.direction,
            "bullish_score":
                result.bullish_score,
            "bearish_score":
                result.bearish_score,
            "neutral_score":
                result.neutral_score,
            "confidence":
                result.confidence,
            "agreement":
                result.agreement,
            "participating_engines":
                result.participating_engines,
            "reasons":
                result.reasons,
        }
