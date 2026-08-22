from __future__ import annotations

from config.settings import settings


def get_ai_api_key() -> str:
    """Return the AI API key from the central application settings."""
    return (settings.ai_api_key or "").strip()


def get_ai_model() -> str:
    """Return the configured AI model from the central application settings."""
    return settings.ai_model.strip()


def get_ai_temperature() -> float:
    """Return the normalized AI temperature from the central settings."""
    return settings.ai_temperature


def is_ai_enabled() -> bool:
    """Return whether the AI layer is enabled and configured with a key."""
    return settings.ai_enabled and bool(get_ai_api_key())
