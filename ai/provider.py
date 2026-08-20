from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ai.context import AIAnalysisContext


@dataclass(frozen=True)
class AIResponse:
    """
    Standard response returned by an AI provider.
    """

    provider: str
    model: str
    summary: str
    direction: str
    confidence: float
    reasoning: list[str]
    warnings: list[str]
    metadata: dict[str, Any]


class AIProvider(ABC):
    """
    Common interface for all AI providers.

    A provider receives both:
    - structured market context
    - a prepared textual prompt
    """

    @abstractmethod
    def analyze(
        self,
        context: AIAnalysisContext,
        prompt: str,
    ) -> AIResponse:
        raise NotImplementedError


class NullAIProvider(AIProvider):
    """
    Safe fallback provider.

    Used when no external AI service is configured.
    It never invents an AI analysis.
    """

    def analyze(
        self,
        context: AIAnalysisContext,
        prompt: str,
    ) -> AIResponse:

        return AIResponse(
            provider="none",
            model="none",
            summary=(
                "No external AI provider is configured."
            ),
            direction=(
                context.confluence_direction
            ),
            confidence=0.0,
            reasoning=[],
            warnings=[
                "AI provider is not configured."
            ],
            metadata={
                "symbol": context.symbol,
                "timeframe": context.timeframe,
                "prompt_length": len(prompt),
            },
        )


class AIProviderManager:
    """
    Manages the active AI provider.

    The rest of the trading system interacts with
    this manager instead of depending directly on
    a specific AI vendor.
    """

    def __init__(
        self,
        provider: AIProvider | None = None,
    ) -> None:

        self._provider = (
            provider
            if provider is not None
            else NullAIProvider()
        )

    @property
    def provider(self) -> AIProvider:
        return self._provider

    def set_provider(
        self,
        provider: AIProvider,
    ) -> None:

        if not isinstance(
            provider,
            AIProvider,
        ):
            raise TypeError(
                "provider must implement AIProvider."
            )

        self._provider = provider

    def analyze(
        self,
        context: AIAnalysisContext,
        prompt: str,
    ) -> AIResponse:

        return self._provider.analyze(
            context,
            prompt,
        )
 
