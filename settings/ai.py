from __future__ import annotations

import os


def get_ai_api_key() -> str:
    """
    Returns the AI API key from environment variables.

    The key must never be hard-coded in source code.
    """

    return os.getenv(
        "AI_API_KEY",
        "",
    ).strip()


def get_ai_model() -> str:
    """
    Returns the configured AI model.
    """

    return os.getenv(
        "AI_MODEL",
        "gpt-5.6-mini",
    ).strip()


def get_ai_temperature() -> float:
    """
    Returns the AI temperature.

    Lower values produce more deterministic responses.
    """

    raw_value = os.getenv(
        "AI_TEMPERATURE",
        "0.2",
    )

    try:
        value = float(raw_value)
    except ValueError:
        value = 0.2

    return max(
        0.0,
        min(
            2.0,
            value,
        ),
    )


def is_ai_enabled() -> bool:
    """
    Determines whether the AI layer is enabled.
    """

    return bool(
        get_ai_api_key()
    )
