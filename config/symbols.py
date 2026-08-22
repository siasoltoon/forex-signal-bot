
"""
Centralized market symbols and timeframe definitions.

The analysis engine should use these normalized identifiers
instead of hard-coding provider-specific symbols throughout
the application.
"""

from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Forex
# ---------------------------------------------------------------------------

FOREX_SYMBOLS: tuple[str, ...] = (
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "USDCHF",
    "AUDUSD",
    "USDCAD",
    "NZDUSD",
    "EURGBP",
    "EURJPY",
    "GBPJPY",
    "EURAUD",
    "EURCAD",
    "EURNZD",
    "EURCHF",
    "GBPAUD",
    "GBPCAD",
    "GBPCHF",
    "GBPNZD",
    "AUDJPY",
    "AUDCAD",
    "AUDCHF",
    "AUDNZD",
    "CADJPY",
    "CADCHF",
    "CHFJPY",
    "NZDJPY",
    "NZDCAD",
    "NZDCHF",
)


# ---------------------------------------------------------------------------
# Crypto
# ---------------------------------------------------------------------------

CRYPTO_SYMBOLS: tuple[str, ...] = (
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "ADAUSDT",
    "DOGEUSDT",
    "AVAXUSDT",
    "DOTUSDT",
    "LINKUSDT",
)


# ---------------------------------------------------------------------------
# Major US stocks
# ---------------------------------------------------------------------------

STOCK_SYMBOLS: tuple[str, ...] = (
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "META",
    "GOOGL",
    "GOOG",
    "TSLA",
    "AVGO",
    "AMD",
    "NFLX",
    "JPM",
    "V",
    "MA",
    "XOM",
    "COST",
    "WMT",
)


# ---------------------------------------------------------------------------
# Indices
# ---------------------------------------------------------------------------

INDEX_SYMBOLS: tuple[str, ...] = (
    "SPX",
    "NDX",
    "DJI",
    "RUT",
)


# ---------------------------------------------------------------------------
# Commodities
# ---------------------------------------------------------------------------

COMMODITY_SYMBOLS: tuple[str, ...] = (
    "XAUUSD",
    "XAGUSD",
    "WTI",
    "BRENT",
)


# ---------------------------------------------------------------------------
# Standard internal timeframes
# ---------------------------------------------------------------------------

TIMEFRAMES: tuple[str, ...] = (
    "1m",
    "5m",
    "15m",
    "30m",
    "1h",
    "4h",
    "1d",
)


# ---------------------------------------------------------------------------
# Higher-level analysis timeframes
# ---------------------------------------------------------------------------

ANALYSIS_TIMEFRAMES: tuple[str, ...] = (
    "1m",
    "5m",
    "15m",
    "30m",
    "1h",
    "4h",
    "1d",
    "1w",
)


# ---------------------------------------------------------------------------
# Multi-timeframe hierarchy
# ---------------------------------------------------------------------------

TIMEFRAME_MINUTES: dict[str, int] = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
    "1w": 10080,
}


@dataclass(frozen=True, slots=True)
class SymbolInfo:
    """
    Metadata describing a supported market symbol.
    """

    symbol: str
    market: str
    provider_symbol_oanda: str | None = None


def normalize_symbol(symbol: str) -> str:
    """
    Normalize a symbol for internal use.

    Examples:
        EUR/USD  -> EURUSD
        eurusd   -> EURUSD
        BTC/USDT -> BTCUSDT
    """

    if not isinstance(symbol, str):
        raise TypeError(
            "symbol must be a string."
        )

    normalized = (
        symbol
        .strip()
        .upper()
        .replace(
            "/",
            "",
        )
        .replace(
            "_",
            "",
        )
        .replace(
            "-",
            "",
        )
    )

    if not normalized:
        raise ValueError(
            "symbol cannot be empty."
        )

    return normalized


def get_market_type(symbol: str) -> str:
    """
    Determine the internal market category of a symbol.

    Returns:
        forex
        crypto
        stock
        index
        commodity
        unknown
    """

    normalized = normalize_symbol(
        symbol
    )

    if normalized in FOREX_SYMBOLS:
        return "forex"

    if normalized in CRYPTO_SYMBOLS:
        return "crypto"

    if normalized in STOCK_SYMBOLS:
        return "stock"

    if normalized in INDEX_SYMBOLS:
        return "index"

    if normalized in COMMODITY_SYMBOLS:
        return "commodity"

    return "unknown"


def is_supported_symbol(
    symbol: str,
) -> bool:
    """
    Check whether a symbol is supported.
    """

    normalized = normalize_symbol(
        symbol
    )

    return normalized in {
        *FOREX_SYMBOLS,
        *CRYPTO_SYMBOLS,
        *STOCK_SYMBOLS,
        *INDEX_SYMBOLS,
        *COMMODITY_SYMBOLS,
    }


def is_supported_timeframe(
    timeframe: str,
) -> bool:
    """
    Check whether an internal timeframe is supported.
    """

    if not isinstance(
        timeframe,
        str,
    ):
        return False

    return (
        timeframe.strip().lower()
        in TIMEFRAME_MINUTES
    )


def normalize_timeframe(
    timeframe: str,
) -> str:
    """
    Normalize common timeframe aliases.

    Examples:
        M15 -> 15m
        H1  -> 1h
        H4  -> 4h
        D   -> 1d
        W   -> 1w
    """

    if not isinstance(
        timeframe,
        str,
    ):
        raise TypeError(
            "timeframe must be a string."
        )

    normalized = (
        timeframe
        .strip()
        .lower()
    )

    aliases = {
        "m1": "1m",
        "1m": "1m",

        "m5": "5m",
        "5m": "5m",

        "m15": "15m",
        "15m": "15m",

        "m30": "30m",
        "30m": "30m",

        "h1": "1h",
        "1h": "1h",

        "h4": "4h",
        "4h": "4h",

        "d": "1d",
        "1d": "1d",

        "w": "1w",
        "1w": "1w",
    }

    result = aliases.get(
        normalized
    )

    if result is None:
        raise ValueError(
            f"Unsupported timeframe: {timeframe}"
        )

    return result


def get_oanda_symbol(
    symbol: str,
) -> str:
    """
    Convert an internal symbol to OANDA's
    currency-pair representation.

    Examples:
        EURUSD -> EUR_USD
        GBPJPY -> GBP_JPY

    For non-forex symbols, the normalized symbol
    is returned unchanged.
    """

    normalized = normalize_symbol(
        symbol
    )

    if (
        normalized in FOREX_SYMBOLS
        and len(normalized) == 6
    ):
        return (
            f"{normalized[:3]}_"
            f"{normalized[3:]}"
        )

    return normalized


def get_all_symbols() -> tuple[str, ...]:
    """
    Return all supported symbols.
    """

    return (
        FOREX_SYMBOLS
        + CRYPTO_SYMBOLS
        + STOCK_SYMBOLS
        + INDEX_SYMBOLS
        + COMMODITY_SYMBOLS
    )


def get_symbols_by_market(
    market: str,
) -> tuple[str, ...]:
    """
    Return symbols belonging to a market category.
    """

    if not isinstance(
        market,
        str,
    ):
        raise TypeError(
            "market must be a string."
        )

    normalized = (
        market
        .strip()
        .lower()
    )

    mapping = {
        "forex": FOREX_SYMBOLS,
        "crypto": CRYPTO_SYMBOLS,
        "stock": STOCK_SYMBOLS,
        "stocks": STOCK_SYMBOLS,
        "index": INDEX_SYMBOLS,
        "indices": INDEX_SYMBOLS,
        "commodity": COMMODITY_SYMBOLS,
        "commodities": COMMODITY_SYMBOLS,
    }

    if normalized not in mapping:
        raise ValueError(
            f"Unknown market category: {market}"
        )

    return mapping[
        normalized
    ]

