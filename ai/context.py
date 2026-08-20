from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AIAnalysisContext:
    """
    Structured context passed to the AI layer.

    The AI receives already-processed market information
    instead of directly controlling the trading system.
    """

    symbol: str
    timeframe: str

    market_regime: str
    market_trend: str
    volatility: str

    confluence_direction: str
    confluence_confidence: float
    confluence_agreement: float

    bullish_score: float
    bearish_score: float
    neutral_score: float

    risk_reward_ratio: float

    analyses: dict[str, Any] = field(
        default_factory=dict
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


class AIContextBuilder:
    """
    Builds a normalized context for the AI layer.
    """

    def build(
        self,
        *,
        symbol: str,
        timeframe: str,
        market_regime: str,
        market_trend: str,
        volatility: str,
        confluence_direction: str,
        confluence_confidence: float,
        confluence_agreement: float,
        bullish_score: float,
        bearish_score: float,
        neutral_score: float,
        risk_reward_ratio: float,
        analyses: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AIAnalysisContext:

        return AIAnalysisContext(
            symbol=symbol,
            timeframe=timeframe,
            market_regime=market_regime,
            market_trend=market_trend,
            volatility=volatility,
            confluence_direction=confluence_direction,
            confluence_confidence=confluence_confidence,
            confluence_agreement=confluence_agreement,
            bullish_score=bullish_score,
            bearish_score=bearish_score,
            neutral_score=neutral_score,
            risk_reward_ratio=risk_reward_ratio,
            analyses=analyses or {},
            metadata=metadata or {},
        )
