
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


# ============================================================================
# Environment helpers
# ============================================================================

def _get_env(
    name: str,
    default: Optional[str] = None,
) -> Optional[str]:
    """
    Read an environment variable safely.

    Empty or whitespace-only values are treated as missing.
    """
    value = os.getenv(name)

    if value is None:
        return default

    value = value.strip()

    return value if value else default


def _get_bool(
    name: str,
    default: bool = False,
) -> bool:
    """
    Read a boolean environment variable safely.

    Accepted true values:
        1, true, yes, on

    Accepted false values:
        0, false, no, off
    """
    value = _get_env(name)

    if value is None:
        return default

    normalized = value.lower()

    if normalized in {"1", "true", "yes", "on"}:
        return True

    if normalized in {"0", "false", "no", "off"}:
        return False

    return default


def _get_int(
    name: str,
    default: int,
) -> int:
    """
    Read an integer environment variable safely.
    """
    value = _get_env(name)

    if value is None:
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _get_float(
    name: str,
    default: float,
) -> float:
    """
    Read a floating-point environment variable safely.
    """
    value = _get_env(name)

    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ============================================================================
# Settings
# ============================================================================

@dataclass(frozen=True)
class Settings:
    """
    Central application configuration.

    Backward-compatible names are intentionally preserved because
    existing project components directly access:

        settings.OANDA_API_KEY
        settings.FINNHUB_API_KEY
        settings.ALPHAVANTAGE_API_KEY

    Telegram components use:

        Settings.load().telegram_token
    """

    # ------------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------------

    app_name: str = "Professional Trading Bot"
    environment: str = "development"
    debug: bool = False

    # ------------------------------------------------------------------------
    # Telegram
    # ------------------------------------------------------------------------

    telegram_token: Optional[str] = None
    telegram_enabled: bool = False

    # ------------------------------------------------------------------------
    # Market Data Providers
    #
    # IMPORTANT:
    # Keep these exact names for backward compatibility.
    # ------------------------------------------------------------------------

    OANDA_API_KEY: Optional[str] = None
    FINNHUB_API_KEY: Optional[str] = None
    ALPHAVANTAGE_API_KEY: Optional[str] = None

    # ------------------------------------------------------------------------
    # Trading / Market configuration
    # ------------------------------------------------------------------------

    default_symbol: str = "EURUSD"
    default_timeframe: str = "1h"

    # ------------------------------------------------------------------------
    # Risk management
    # ------------------------------------------------------------------------

    risk_per_trade: float = 0.01
    max_open_positions: int = 5

    # ------------------------------------------------------------------------
    # System
    # ------------------------------------------------------------------------

    timezone: str = "UTC"
    log_level: str = "INFO"

    # ------------------------------------------------------------------------
    # AI / Analysis
    # ------------------------------------------------------------------------

    ai_enabled: bool = True

    # ------------------------------------------------------------------------
    # Networking
    # ------------------------------------------------------------------------

    request_timeout: int = 30
    max_retries: int = 3

    # =========================================================================
    # Loader
    # =========================================================================

    @classmethod
    def load(cls) -> "Settings":
        """
        Load configuration from environment variables.

        This method intentionally does NOT use lru_cache.

        Why?
        -------
        Unit tests may temporarily modify environment variables using
        pytest.monkeypatch. Caching the Settings object would cause old
        environment values to remain active after the variables are removed.

        Therefore every call to Settings.load() reads the current
        environment state.
        """

        # --------------------------------------------------------------------
        # Telegram
        # --------------------------------------------------------------------

        telegram_token = _get_env(
            "TELEGRAM_BOT_TOKEN",
        )

        # --------------------------------------------------------------------
        # Create settings
        # --------------------------------------------------------------------

        return cls(
            # =================================================================
            # Application
            # =================================================================

            app_name=_get_env(
                "APP_NAME",
                "Professional Trading Bot",
            ),

            environment=_get_env(
                "ENVIRONMENT",
                "development",
            ),

            debug=_get_bool(
                "DEBUG",
                False,
            ),

            # =================================================================
            # Telegram
            # =================================================================

            telegram_token=telegram_token,

            telegram_enabled=bool(
                telegram_token
            ),

            # =================================================================
            # Market Data APIs
            # =================================================================

            OANDA_API_KEY=_get_env(
                "OANDA_API_KEY",
            ),

            FINNHUB_API_KEY=_get_env(
                "FINNHUB_API_KEY",
            ),

            ALPHAVANTAGE_API_KEY=_get_env(
                "ALPHAVANTAGE_API_KEY",
            ),

            # =================================================================
            # Trading
            # =================================================================

            default_symbol=_get_env(
                "DEFAULT_SYMBOL",
                "EURUSD",
            ),

            default_timeframe=_get_env(
                "DEFAULT_TIMEFRAME",
                "1h",
            ),

            # =================================================================
            # Risk management
            # =================================================================

            risk_per_trade=_get_float(
                "RISK_PER_TRADE",
                0.01,
            ),

            max_open_positions=_get_int(
                "MAX_OPEN_POSITIONS",
                5,
            ),

            # =================================================================
            # System
            # =================================================================

            timezone=_get_env(
                "TIMEZONE",
                "UTC",
            ),

            log_level=_get_env(
                "LOG_LEVEL",
                "INFO",
            ),

            # =================================================================
            # AI
            # =================================================================

            ai_enabled=_get_bool(
                "AI_ENABLED",
                True,
            ),

            # =================================================================
            # Networking
            # =================================================================

            request_timeout=_get_int(
                "REQUEST_TIMEOUT",
                30,
            ),

            max_retries=_get_int(
                "MAX_RETRIES",
                3,
            ),
        )


# ============================================================================
# Global settings instance
# ============================================================================
#
# Existing project code can continue using:
#
#     from config.settings import settings
#
# and:
#
#     settings.OANDA_API_KEY
#     settings.FINNHUB_API_KEY
#     settings.ALPHAVANTAGE_API_KEY
#
# ============================================================================

settings = Settings.load()


# ============================================================================
# Public exports
# ============================================================================

__all__ = [
    "Settings",
    "settings",
]

