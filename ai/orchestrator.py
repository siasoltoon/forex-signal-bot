from __future__ import annotations

from ai.context import AIAnalysisContext
from ai.parser import AIResponseParser
from ai.provider import AIProvider, AIResponse
from ai.prompt_builder import AIPromptBuilder


class AIOrchestrator:
    """
    Coordinates the complete AI analysis pipeline.

    Pipeline:

        Analysis Context
              ↓
        Prompt Builder
              ↓
        AI Provider
              ↓
        Response Parser

    This class does not execute trades.
    """

    def __init__(
        self,
        provider: AIProvider,
        prompt_builder: AIPromptBuilder | None = None,
        parser: AIResponseParser | None = None,
    ) -> None:

        if not isinstance(
            provider,
            AIProvider,
        ):
            raise TypeError(
                "provider must implement AIProvider."
            )

        self.provider = provider

        self.prompt_builder = (
            prompt_builder
            if prompt_builder is not None
            else AIPromptBuilder()
        )

        self.parser = (
            parser
            if parser is not None
            else AIResponseParser()
        )

    def analyze(
        self,
        context: AIAnalysisContext,
    ) -> AIResponse:

        # Build the structured prompt.
        prompt = (
            self.prompt_builder.build(
                context
            )
        )

        # The current provider interface receives
        # structured context. The prompt is kept available
        # for providers that need textual input.
        response = self.provider.analyze(
            context
        )

        # If the provider already returns a normalized
        # AIResponse, return it directly.
        if isinstance(
            response,
            AIResponse,
        ):
            return response

        # Defensive fallback for custom providers.
        return self.parser.parse(
            str(response),
            provider=self.provider.__class__.__name__,
            model="unknown",
        )

    def build_prompt(
        self,
        context: AIAnalysisContext,
    ) -> str:

        return self.prompt_builder.build(
            context
        )
