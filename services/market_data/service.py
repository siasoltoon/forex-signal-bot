from __future__ import annotations

from data.manager import DataManager
from data.models import Candle

from core.errors import ApplicationError
from core.logger import setup_logger


logger = setup_logger()


class MarketDataService:
    """
    High-level market-data service.

    This layer is the stable interface between the application's analysis
    systems and the lower-level data infrastructure.

    Responsibilities
    ----------------
    - Validate market-data requests.
    - Keep provider/data-manager details out of analysis code.
    - Forward optional explicit provider selection.
    - Preserve the normalized Candle contract returned by DataManager.
    - Convert unexpected infrastructure failures into ApplicationError.
    - Provide a small, stable API for indicators, strategies and AI.

    Provider selection, retry, fallback and provider health remain the
    responsibility of the data layer; this service must not duplicate them.
    """

    _DEFAULT_LIMIT = 100
    _MAX_LIMIT = 5000

    def __init__(self, data_manager: DataManager) -> None:
        if data_manager is None:
            raise TypeError("data_manager cannot be None.")

        self.data_manager = data_manager

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = _DEFAULT_LIMIT,
        provider_name: str | None = None,
    ) -> list[Candle]:
        """
        Retrieve normalized market candles.

        ``provider_name=None`` delegates provider selection to DataManager.
        An explicit provider name is forwarded unchanged so aliases and
        provider-specific normalization remain centralized in the data layer.
        """

        normalized_symbol, normalized_timeframe = self._validate_request(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            provider_name=provider_name,
        )

        try:
            candles = await self.data_manager.get_candles(
                provider_name=provider_name,
                symbol=normalized_symbol,
                timeframe=normalized_timeframe,
                limit=limit,
            )
        except ApplicationError:
            raise
        except Exception as error:
            logger.exception(
                "MarketDataService failed. "
                "symbol=%s timeframe=%s provider=%s limit=%s",
                normalized_symbol,
                normalized_timeframe,
                provider_name,
                limit,
            )

            raise ApplicationError(
                "Market data service failed.",
                {
                    "symbol": normalized_symbol,
                    "timeframe": normalized_timeframe,
                    "limit": limit,
                    "provider": provider_name,
                },
            ) from error

        if candles is None:
            logger.warning(
                "Market data manager returned None for %s (%s).",
                normalized_symbol,
                normalized_timeframe,
            )
            return []

        if not isinstance(candles, list):
            raise ApplicationError(
                "Market data manager returned invalid candle data.",
                {
                    "symbol": normalized_symbol,
                    "timeframe": normalized_timeframe,
                    "provider": provider_name,
                },
            )

        if not candles:
            logger.warning(
                "No candles returned for %s (%s).",
                normalized_symbol,
                normalized_timeframe,
            )
            return []

        # DataManager/provider layers own Candle normalization.  We only
        # enforce the public service contract here without rebuilding the
        # normalization pipeline a second time.
        return candles

    async def get_candles_with_fallback(
        self,
        symbol: str,
        timeframe: str,
        limit: int = _DEFAULT_LIMIT,
        providers: list[str] | tuple[str, ...] | None = None,
    ) -> list[Candle]:
        """
        Retrieve candles using DataManager's provider fallback mechanism.

        Keeping fallback here as a thin delegation prevents analysis layers
        from needing to know which component owns provider failover.
        """

        normalized_symbol, normalized_timeframe = self._validate_request(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        if not hasattr(
            self.data_manager,
            "get_candles_with_fallback",
        ):
            raise ApplicationError(
                "Data manager does not support provider fallback."
            )

        try:
            candles = await self.data_manager.get_candles_with_fallback(
                symbol=normalized_symbol,
                timeframe=normalized_timeframe,
                limit=limit,
                providers=providers,
            )
        except ApplicationError:
            raise
        except Exception as error:
            logger.exception(
                "MarketDataService fallback request failed. "
                "symbol=%s timeframe=%s",
                normalized_symbol,
                normalized_timeframe,
            )

            raise ApplicationError(
                "Market data fallback service failed.",
                {
                    "symbol": normalized_symbol,
                    "timeframe": normalized_timeframe,
                    "limit": limit,
                    "providers": providers,
                },
            ) from error

        if not isinstance(candles, list):
            raise ApplicationError(
                "Market data fallback returned invalid candle data.",
                {
                    "symbol": normalized_symbol,
                    "timeframe": normalized_timeframe,
                },
            )

        return candles

    @staticmethod
    def _validate_request(
        symbol: str,
        timeframe: str,
        limit: int,
        provider_name: str | None = None,
    ) -> tuple[str, str]:
        """
        Validate and normalize a market-data request.

        Returns the canonicalized symbol and timeframe while keeping provider
        normalization centralized in the provider/data-manager layer.
        """

        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string.")

        normalized_symbol = symbol.strip().upper()
        if not normalized_symbol:
            raise ValueError("symbol cannot be empty.")

        if not isinstance(timeframe, str):
            raise TypeError("timeframe must be a string.")

        normalized_timeframe = timeframe.strip().upper()
        if not normalized_timeframe:
            raise ValueError("timeframe cannot be empty.")

        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError("limit must be an integer.")

        if limit < 1:
            raise ValueError("limit must be greater than zero.")

        if limit > MarketDataService._MAX_LIMIT:
            raise ValueError(
                f"limit cannot be greater than "
                f"{MarketDataService._MAX_LIMIT}."
            )

        if provider_name is not None:
            if not isinstance(provider_name, str):
                raise TypeError("provider_name must be a string or None.")
            if not provider_name.strip():
                raise ValueError("provider_name cannot be empty.")

        return normalized_symbol, normalized_timeframe
