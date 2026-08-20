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
        AI Response
              ↓
        Standardized Result
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

    def build_prompt(
        self,
        context: AIAnalysisContext,
    ) -> str:

        return self.prompt_builder.build(
            context
        )

    def analyze(
        self,
        context: AIAnalysisContext,
    ) -> AIResponse:

        prompt = self.build_prompt(
            context
        )

        response = self.provider.analyze(
            context,
            prompt,
        )

        if not isinstance(
            response,
            AIResponse,
        ):
            return self.parser.parse(
                str(response),
                provider=(
                    self.provider.__class__.__name__
                ),
                model="unknown",
            )

        return response
