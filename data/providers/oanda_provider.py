from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from typing import Final, Any

from core.errors import ApplicationError
from core.logger import setup_logger

from data.base import MarketDataProvider
from data.models import Candle
from data.providers.clients.oanda import OandaClient


logger = setup_logger()


class OandaProvider(MarketDataProvider):
    """
    Production-grade OANDA market data provider.

    Responsibilities
    ----------------
    - Validate request parameters.
    - Normalize symbols and timeframes.
    - Communicate with OandaClient.
    - Validate OANDA responses.
    - Ignore incomplete candles.
    - Convert valid OANDA candles into Candle models.
    - Normalize timestamps to UTC.
    - Validate OHLC and volume values.
    - Remove duplicate timestamps.
    - Preserve chronological ordering.
    - Return at most `limit` candles.
    - Convert unexpected provider/client failures into ApplicationError.

    Public API is intentionally kept compatible with the existing project.
    """

    name = "oanda"

    # ------------------------------------------------------------------
    # Supported OANDA timeframes
    # ------------------------------------------------------------------

    _TIMEFRAME_ALIASES: Final[dict[str, str]] = {
        "M1": "M1",
        "M2": "M2",
        "M4": "M4",
        "M5": "M5",
        "M10": "M10",
        "M15": "M15",
        "M30": "M30",

        "H1": "H1",
        "H2": "H2",
        "H3": "H3",
        "H4": "H4",
        "H6": "H6",
        "H8": "H8",
        "H12": "H12",

        "D": "D",
        "W": "W",
        "M": "M",
    }

    _MAX_LIMIT: Final[int] = 5000

    # ------------------------------------------------------------------
    # Constructor
    # ------------------------------------------------------------------

    def __init__(
        self,
        client: OandaClient | None = None,
    ) -> None:
        """
        Create an OANDA provider.

        Dependency injection is supported so tests and future
        infrastructure can provide a custom client.
        """

        self.client = (
            client
            if client is not None
            else OandaClient()
        )

    # ------------------------------------------------------------------
    # Timeframe normalization
    # ------------------------------------------------------------------

    @classmethod
    def _normalize_timeframe(
        cls,
        timeframe: str,
    ) -> str:
        """
        Normalize a user-facing timeframe into an OANDA granularity.

        Examples
        --------
        h1 -> H1
        H1 -> H1
        m15 -> M15
        """

        if not isinstance(timeframe, str):
            raise TypeError(
                "timeframe must be a string."
            )

        normalized = timeframe.strip().upper()

        if not normalized:
            raise ValueError(
                "timeframe cannot be empty."
            )

        result = cls._TIMEFRAME_ALIASES.get(
            normalized
        )

        if result is None:
            raise ValueError(
                f"Unsupported OANDA timeframe: {timeframe}"
            )

        return result

    # ------------------------------------------------------------------
    # Request validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_request(
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> None:
        """
        Validate market-data request arguments.
        """

        if not isinstance(symbol, str):
            raise TypeError(
                "symbol must be a string."
            )

        if not symbol.strip():
            raise ValueError(
                "symbol cannot be empty."
            )

        if not isinstance(timeframe, str):
            raise TypeError(
                "timeframe must be a string."
            )

        if not timeframe.strip():
            raise ValueError(
                "timeframe cannot be empty."
            )

        if not isinstance(limit, int):
            raise TypeError(
                "limit must be an integer."
            )

        if isinstance(limit, bool):
            raise TypeError(
                "limit must be an integer."
            )

        if limit < 1:
            raise ValueError(
                "limit must be greater than zero."
            )

        if limit > OandaProvider._MAX_LIMIT:
            raise ValueError(
                f"limit cannot exceed "
                f"{OandaProvider._MAX_LIMIT}."
            )

    # ------------------------------------------------------------------
    # Timestamp parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_timestamp(
        value: object,
    ) -> datetime:
        """
        Parse an OANDA timestamp and normalize it to UTC.
        """

        if not isinstance(value, str):
            raise TypeError(
                "OANDA candle timestamp must be a string."
            )

        timestamp_text = value.strip()

        if not timestamp_text:
            raise ValueError(
                "OANDA candle timestamp cannot be empty."
            )

        # OANDA commonly returns ISO-8601 timestamps ending in Z.
        if timestamp_text.endswith("Z"):
            timestamp_text = (
                timestamp_text[:-1] + "+00:00"
            )

        timestamp = datetime.fromisoformat(
            timestamp_text
        )

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(
                tzinfo=timezone.utc
            )

        return timestamp.astimezone(
            timezone.utc
        )

    # ------------------------------------------------------------------
    # Numeric parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_price(
        value: object,
    ) -> float:
        """
        Convert and validate a price.
        """

        try:
            price = float(value)
        except (
            TypeError,
            ValueError,
            OverflowError,
        ) as error:
            raise ValueError(
                "Price must be a valid number."
            ) from error

        if not isfinite(price):
            raise ValueError(
                "Price must be finite."
            )

        if price <= 0:
            raise ValueError(
                "Price must be greater than zero."
            )

        return price

    @staticmethod
    def _parse_volume(
        value: object,
    ) -> float:
        """
        Convert and validate candle volume.

        Missing volume is normalized to 0.0 because
        OANDA candle volume is not guaranteed to be
        present in every mocked or alternative payload.
        """

        if value is None:
            return 0.0

        try:
            volume = float(value)
        except (
            TypeError,
            ValueError,
            OverflowError,
        ) as error:
            raise ValueError(
                "Volume must be a valid number."
            ) from error

        if not isfinite(volume):
            raise ValueError(
                "Volume must be finite."
            )

        if volume < 0:
            raise ValueError(
                "Volume cannot be negative."
            )

        return volume

    # ------------------------------------------------------------------
    # OHLC validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_ohlc(
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
    ) -> None:
        """
        Validate OHLC structural consistency.

        Required relationship:

            high >= max(open, close)
            low  <= min(open, close)
            high >= low
        """

        if high_price < low_price:
            raise ValueError(
                "High price cannot be lower than low price."
            )

        if high_price < max(
            open_price,
            close_price,
        ):
            raise ValueError(
                "High price must be greater than or equal "
                "to open and close."
            )

        if low_price > min(
            open_price,
            close_price,
        ):
            raise ValueError(
                "Low price must be lower than or equal "
                "to open and close."
            )

    # ------------------------------------------------------------------
    # Candle conversion
    # ------------------------------------------------------------------

    def _convert_candle(
        self,
        item: object,
        symbol: str,
    ) -> Candle | None:
        """
        Convert one raw OANDA candle into a Candle model.

        Invalid individual candles are skipped rather than
        destroying the entire provider response.
        """

        if not isinstance(item, dict):
            logger.warning(
                "Skipping invalid OANDA candle payload."
            )
            return None

        # --------------------------------------------------------------
        # Ignore currently forming candle.
        # --------------------------------------------------------------

        if not item.get(
            "complete",
            False,
        ):
            return None

        # --------------------------------------------------------------
        # OANDA normally provides midpoint prices under `mid`.
        # --------------------------------------------------------------

        price = item.get("mid")

        if not isinstance(price, dict):
            logger.warning(
                "Skipping OANDA candle without "
                "mid prices."
            )
            return None

        try:
            timestamp = self._parse_timestamp(
                item.get("time")
            )

            open_price = self._parse_price(
                price["o"]
            )

            high_price = self._parse_price(
                price["h"]
            )

            low_price = self._parse_price(
                price["l"]
            )

            close_price = self._parse_price(
                price["c"]
            )

            volume = self._parse_volume(
                item.get("volume", 0)
            )

            self._validate_ohlc(
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
            )

            return Candle(
                symbol=symbol,
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
            )

        except (
            KeyError,
            TypeError,
            ValueError,
            OverflowError,
        ) as error:

            logger.warning(
                "Skipping invalid OANDA candle: %s",
                error,
            )

            return None

    # ------------------------------------------------------------------
    # Response validation
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_candles(
        response: object,
        symbol: str,
    ) -> list[Any]:
        """
        Validate and extract the raw candle list
        from an OANDA response.
        """

        if not isinstance(response, dict):
            raise ApplicationError(
                "Invalid OANDA response.",
                {
                    "provider": "oanda",
                    "symbol": symbol,
                },
            )

        raw_candles = response.get(
            "candles"
        )

        if raw_candles is None:
            raise ApplicationError(
                "OANDA response does not contain candles.",
                {
                    "provider": "oanda",
                    "symbol": symbol,
                },
            )

        if not isinstance(
            raw_candles,
            list,
        ):
            raise ApplicationError(
                "Invalid OANDA candles payload.",
                {
                    "provider": "oanda",
                    "symbol": symbol,
                },
            )

        return raw_candles

    # ------------------------------------------------------------------
    # Deduplication
    # ------------------------------------------------------------------

    @staticmethod
    def _deduplicate_candles(
        candles: list[Candle],
    ) -> list[Candle]:
        """
        Remove duplicate candles using timestamp as the
        canonical candle identity.

        The latest occurrence wins.
        """

        unique: dict[
            datetime,
            Candle,
        ] = {}

        for candle in candles:
            unique[candle.timestamp] = candle

        return list(
            unique.values()
        )

    # ------------------------------------------------------------------
    # Main public API
    # ------------------------------------------------------------------

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[Candle]:
        """
        Fetch and normalize OANDA candles.

        Parameters
        ----------
        symbol:
            OANDA instrument such as EUR_USD.

        timeframe:
            OANDA timeframe such as M1, M15, H1, H4.

        limit:
            Maximum number of candles to return.

        Returns
        -------
        list[Candle]
            Valid, complete, chronologically ordered candles.
        """

        # --------------------------------------------------------------
        # Validate request.
        # --------------------------------------------------------------

        self._validate_request(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        normalized_symbol = (
            symbol.strip().upper()
        )

        normalized_timeframe = (
            self._normalize_timeframe(
                timeframe
            )
        )

        # --------------------------------------------------------------
        # Fetch data.
        # --------------------------------------------------------------

        try:
            response = await self.client.get_candles(
                instrument=normalized_symbol,
                granularity=normalized_timeframe,
                count=limit,
            )

        except Exception as error:
            logger.exception(
                "OANDA candle request failed "
                "for %s.",
                normalized_symbol,
            )

            raise ApplicationError(
                "Failed to fetch OANDA candles.",
                {
                    "provider": self.name,
                    "symbol": normalized_symbol,
                    "timeframe": normalized_timeframe,
                    "limit": limit,
                },
            ) from error

        # --------------------------------------------------------------
        # Validate response.
        # --------------------------------------------------------------

        raw_candles = self._extract_candles(
            response=response,
            symbol=normalized_symbol,
        )

        # --------------------------------------------------------------
        # Convert valid candles.
        # --------------------------------------------------------------

        candles: list[Candle] = []

        for item in raw_candles:
            candle = self._convert_candle(
                item=item,
                symbol=normalized_symbol,
            )

            if candle is not None:
                candles.append(candle)

        # --------------------------------------------------------------
        # Remove duplicates.
        # --------------------------------------------------------------

        candles = self._deduplicate_candles(
            candles
        )

        # --------------------------------------------------------------
        # Chronological ordering.
        # --------------------------------------------------------------

        candles.sort(
            key=lambda candle: candle.timestamp
        )

        # --------------------------------------------------------------
        # Enforce final limit.
        #
        # We keep the newest candles.
        # --------------------------------------------------------------

        if len(candles) > limit:
            candles = candles[-limit:]

        logger.info(
            "OANDA returned %d valid candles "
            "for %s (%s).",
            len(candles),
            normalized_symbol,
            normalized_timeframe,
        )

        return candles


__all__ = [
    "OandaProvider",
]
