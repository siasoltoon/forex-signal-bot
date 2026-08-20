from __future__ import annotations

import json
from typing import Any

from ai.provider import AIResponse


class AIResponseParser:
    """
    Converts raw AI responses into a standardized AIResponse.

    The parser is intentionally defensive because AI output
    may be incomplete, malformed, or differently formatted.
    """

    VALID_DIRECTIONS = {
        "bullish",
        "bearish",
        "neutral",
    }

    def parse(
        self,
        raw_response: str,
        *,
        provider: str,
        model: str,
    ) -> AIResponse:

        if not isinstance(
            raw_response,
            str,
        ):
            raise TypeError(
                "raw_response must be a string."
            )

        text = raw_response.strip()

        if not text:
            raise ValueError(
                "AI response cannot be empty."
            )

        parsed = self._try_parse_json(
            text
        )

        if parsed is None:
            return self._fallback_response(
                text,
                provider=provider,
                model=model,
            )

        return self._build_response(
            parsed,
            provider=provider,
            model=model,
        )

    def _try_parse_json(
        self,
        text: str,
    ) -> dict[str, Any] | None:

        candidates = [
            text,
            self._extract_code_block(text),
        ]

        for candidate in candidates:

            if not candidate:
                continue

            try:

                data = json.loads(
                    candidate
                )

                if isinstance(
                    data,
                    dict,
                ):
                    return data

            except (
                json.JSONDecodeError,
                TypeError,
            ):
                continue

        return None

    @staticmethod
    def _extract_code_block(
        text: str,
    ) -> str | None:

        if "```" not in text:
            return None

        parts = text.split(
            "```"
        )

        if len(parts) < 3:
            return None

        content = parts[1].strip()

        if content.startswith(
            "json"
        ):
            content = content[4:].strip()

        return content

    def _normalize_direction(
        self,
        value: Any,
    ) -> str:

        if not isinstance(
            value,
            str,
        ):
            return "neutral"

        direction = (
            value.strip()
            .lower()
        )

        aliases = {
            "buy": "bullish",
            "long": "bullish",
            "up": "bullish",
            "sell": "bearish",
            "short": "bearish",
            "down": "bearish",
            "flat": "neutral",
            "none": "neutral",
        }

        direction = aliases.get(
            direction,
            direction,
        )

        if direction not in (
            self.VALID_DIRECTIONS
        ):
            return "neutral"

        return direction

    @staticmethod
    def _normalize_confidence(
        value: Any,
    ) -> float:

        try:
            confidence = float(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

        if confidence > 1:
            confidence /= 100.0

        return max(
            0.0,
            min(
                1.0,
                confidence,
            ),
        )

    @staticmethod
    def _normalize_list(
        value: Any,
    ) -> list[str]:

        if isinstance(
            value,
            list,
        ):
            return [
                str(item)
                for item in value
            ]

        if isinstance(
            value,
            str,
        ):
            return [value]

        return []

    def _build_response(
        self,
        data: dict[str, Any],
        *,
        provider: str,
        model: str,
    ) -> AIResponse:

        direction = (
            self._normalize_direction(
                data.get(
                    "direction"
                )
            )
        )

        confidence = (
            self._normalize_confidence(
                data.get(
                    "confidence",
                    0.0,
                )
            )
        )

        summary = data.get(
            "summary",
            "",
        )

        if not isinstance(
            summary,
            str,
        ):
            summary = str(
                summary
            )

        reasoning = (
            self._normalize_list(
                data.get(
                    "reasoning",
                    [],
                )
            )
        )

        warnings = (
            self._normalize_list(
                data.get(
                    "warnings",
                    [],
                )
            )
        )

        metadata = data.get(
            "metadata",
            {},
        )

        if not isinstance(
            metadata,
            dict,
        ):
            metadata = {}

        return AIResponse(
            provider=provider,
            model=model,
            summary=summary.strip(),
            direction=direction,
            confidence=confidence,
            reasoning=reasoning,
            warnings=warnings,
            metadata=metadata,
        )

    def _fallback_response(
        self,
        text: str,
        *,
        provider: str,
        model: str,
    ) -> AIResponse:

        return AIResponse(
            provider=provider,
            model=model,
            summary=text,
            direction="neutral",
            confidence=0.0,
            reasoning=[],
            warnings=[
                "AI response was not valid JSON."
            ],
            metadata={
                "raw_format": True,
            },
        )
