from __future__ import annotations

from typing import Any

from ai.context import AIAnalysisContext
from ai.provider import AIProvider, AIResponse


class OpenAIProvider(AIProvider):
    """
    OpenAI-backed AI provider.

    The actual API client is initialized lazily so that the
    rest of the application can still start when AI is disabled.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float = 0.2,
    ) -> None:

        if not api_key.strip():
            raise ValueError(
                "OpenAI API key cannot be empty."
            )

        if not model.strip():
            raise ValueError(
                "OpenAI model cannot be empty."
            )

        self.api_key = api_key.strip()
        self.model = model.strip()
        self.temperature = temperature

        self._client: Any | None = None

    def _get_client(self) -> Any:

        if self._client is not None:
            return self._client

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "OpenAI SDK is not installed."
            ) from exc

        self._client = OpenAI(
            api_key=self.api_key
        )

        return self._client

    def analyze(
        self,
        context: AIAnalysisContext,
        prompt: str,
    ) -> AIResponse:

        client = self._get_client()

        response = client.responses.create(
            model=self.model,
            instructions=(
                "You are a professional financial "
                "market-analysis assistant. "
                "Do not claim certainty. "
                "Do not execute trades."
            ),
            input=prompt,
        )

        text = getattr(
            response,
            "output_text",
            "",
        )

        if not text:
            raise RuntimeError(
                "OpenAI returned an empty response."
            )

        return AIResponse(
            provider="openai",
            model=self.model,
            summary=text,
            direction=(
                context.confluence_direction
            ),
            confidence=(
                context.confluence_confidence
            ),
            reasoning=[],
            warnings=[],
            metadata={
                "symbol": context.symbol,
                "timeframe": context.timeframe,
                "temperature": self.temperature,
            },
        )
