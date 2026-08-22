from __future__ import annotations

from core.errors import ApplicationError
from data.base import MarketDataProvider
from data.models import Candle
from data.provider_manager import ProviderManager


class ExplicitProviderManager(ProviderManager):
    """Public single-provider contract used by DataManager.

    This adapter keeps explicit-provider semantics separate from the
    fallback-oriented ProviderManager.get_candles() contract.
    """

    async def get_candles_explicit(
        self,
        provider: MarketDataProvider,
        *,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> list[Candle]:
        """Fetch one provider without fallback and allow an empty result."""
        if not provider.is_configured():
            raise ApplicationError(
                f"Market data provider is not configured: {provider.name}"
            )

        self._last_failures.clear()

        try:
            candles = await self._request_with_retry(
                provider.name,
                provider,
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
            )
        except Exception as error:
            if getattr(error, "message", None) == "Provider returned no candles.":
                return []
            raise

        return self._normalize_candles(candles, limit=limit)


__all__ = ["ExplicitProviderManager"]
