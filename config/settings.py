from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value if value else default


def _get_bool(name: str, default: bool = False) -> bool:
    value = _get_env(name)
    if value is None:
        return default
    normalized = value.lower()
    if normalized in {"1", "true", "yes", "y", "on", "enabled"}:
        return True
    if normalized in {"0", "false", "no", "n", "off", "disabled"}:
        return False
    raise ValueError(f"Invalid boolean value for '{name}': {value}")


def _get_int(name: str, default: int) -> int:
    value = _get_env(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(f"Invalid integer value for '{name}': {value}") from error


def _get_float(name: str, default: float) -> float:
    value = _get_env(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError as error:
        raise ValueError(f"Invalid float value for '{name}': {value}") from error


def _get_list(name: str, default: list[str] | None = None, separator: str = ",") -> list[str]:
    if not separator:
        raise ValueError("Environment list separator cannot be empty.")
    value = _get_env(name)
    if value is None:
        return list(default or [])
    return [item.strip() for item in value.split(separator) if item.strip()]


def get_env(key: str, default: str | None = None) -> str | None:
    if not isinstance(key, str):
        raise TypeError("Environment key must be a string.")
    key = key.strip()
    if not key:
        raise ValueError("Environment key cannot be empty.")
    return _get_env(key, default)


def get_required_env(key: str) -> str:
    value = get_env(key)
    if value is None:
        raise RuntimeError(f"Required environment variable '{key}' is not configured.")
    return value


def get_bool_env(key: str, default: bool = False) -> bool:
    return _get_bool(key, default)


def get_int_env(key: str, default: int) -> int:
    return _get_int(key, default)


def get_float_env(key: str, default: float) -> float:
    return _get_float(key, default)


def get_list_env(key: str, default: list[str] | None = None, separator: str = ",") -> list[str]:
    return _get_list(key, default, separator)


@dataclass(frozen=True)
class Settings:
    app_name: str = "Professional Trading Bot"
    environment: str = "development"
    debug: bool = False
    telegram_token: Optional[str] = None
    telegram_enabled: bool = False
    OANDA_API_KEY: Optional[str] = None
    FINNHUB_API_KEY: Optional[str] = None
    ALPHAVANTAGE_API_KEY: Optional[str] = None
    default_symbol: str = "EURUSD"
    default_timeframe: str = "1h"
    risk_per_trade: float = 0.01
    max_open_positions: int = 5
    timezone: str = "UTC"
    log_level: str = "INFO"
    ai_enabled: bool = True
    ai_api_key: Optional[str] = None
    ai_model: str = "gpt-5.6-luna"
    ai_temperature: float = 0.2
    request_timeout: int = 30
    max_retries: int = 3

    @classmethod
    def load(cls) -> "Settings":
        telegram_token = _get_env("TELEGRAM_BOT_TOKEN")
        ai_api_key = _get_env("AI_API_KEY")
        ai_enabled = _get_bool("AI_ENABLED", bool(ai_api_key))
        ai_temperature = max(0.0, min(2.0, _get_float("AI_TEMPERATURE", 0.2)))
        return cls(
            app_name=_get_env("APP_NAME", "Professional Trading Bot"),
            environment=_get_env("ENVIRONMENT", "development"),
            debug=_get_bool("DEBUG", False),
            telegram_token=telegram_token,
            telegram_enabled=bool(telegram_token),
            OANDA_API_KEY=_get_env("OANDA_API_KEY"),
            FINNHUB_API_KEY=_get_env("FINNHUB_API_KEY"),
            ALPHAVANTAGE_API_KEY=_get_env("ALPHAVANTAGE_API_KEY"),
            default_symbol=_get_env("DEFAULT_SYMBOL", "EURUSD"),
            default_timeframe=_get_env("DEFAULT_TIMEFRAME", "1h"),
            risk_per_trade=_get_float("RISK_PER_TRADE", 0.01),
            max_open_positions=_get_int("MAX_OPEN_POSITIONS", 5),
            timezone=_get_env("TIMEZONE", "UTC"),
            log_level=_get_env("LOG_LEVEL", "INFO"),
            ai_enabled=ai_enabled,
            ai_api_key=ai_api_key,
            ai_model=_get_env("AI_MODEL", "gpt-5.6-luna"),
            ai_temperature=ai_temperature,
            request_timeout=_get_int("REQUEST_TIMEOUT", 30),
            max_retries=_get_int("MAX_RETRIES", 3),
        )


settings = Settings.load()

__all__ = [
    "Settings", "settings", "get_env", "get_required_env",
    "get_bool_env", "get_int_env", "get_float_env", "get_list_env",
]
