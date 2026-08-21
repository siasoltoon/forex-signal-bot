from __future__ import annotations

from analysis import (
    AnalysisResult,
    AnalysisScorer,
)


def test_bullish_score_returns_buy() -> None:
    scorer = AnalysisScorer()

    result = AnalysisResult(
        trend="bullish",
        momentum="neutral",
        indicators={},
    )

    score = scorer.score(
        result
    )

    assert score.direction == "BUY"

    assert score.score == 30

    assert score.confidence == 0.3



def test_bearish_score_returns_sell() -> None:
    scorer = AnalysisScorer()

    result = AnalysisResult(
        trend="bearish",
        momentum="neutral",
        indicators={},
    )

    score = scorer.score(
        result
    )

    assert score.direction == "SELL"

    assert score.score == -30

    assert score.confidence == 0.3



def test_oversold_momentum_adds_positive_score() -> None:
    scorer = AnalysisScorer()

    result = AnalysisResult(
        trend="sideways",
        momentum="oversold",
        indicators={},
    )

    score = scorer.score(
        result
    )

    assert score.score == 20

    assert score.direction == "BUY"



def test_overbought_momentum_adds_negative_score() -> None:
    scorer = AnalysisScorer()

    result = AnalysisResult(
        trend="sideways",
        momentum="overbought",
        indicators={},
    )

    score = scorer.score(
        result
    )

    assert score.score == -20

    assert score.direction == "SELL"



def test_neutral_analysis() -> None:
    scorer = AnalysisScorer()

    result = AnalysisResult(
        trend="sideways",
        momentum="neutral",
        indicators={},
    )

    score = scorer.score(
        result
    )

    assert score.score == 0

    assert score.direction == "NEUTRAL"

    assert score.confidence == 0
