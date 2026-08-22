
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Iterable

from core.errors import ApplicationError
from core.logger import setup_logger

from data.base import MarketDataProvider
from data.factory import ProviderFactory
from data.models import Candle


logger = setup_logger()


@dataclass(frozen=True, slots=True)
class ProviderFailure:
    """
    Information about a failed provider attempt.
    """

    provider: str
    attempt: int
    error_type: str
    message: str


class ProviderManager:
    """
    High-level manager for market-data providers.

    Responsibilities
    ----------------
    - Manage provider priority.
    - Create providers through ProviderFactory.
    - Retry temporary provider failures.
    - Fall back to the next provider.
    - Keep provider failures isolated.
    - Validate the final candle result.
    - Preserve the common MarketDataProvider contract.

    The manager does NOT modify provider implementations.

    Example
    -------
        manager = ProviderManager(
            providers=[
                "oanda",
                "finnhub",
                "alphavantage",
            ]
        )

        candles = await manager.get_candles(
            symbol="EUR_USD",
            timeframe="M15",
            limit=100,
        )
    """

    DEFAULT_PROVIDERS: tuple[str, ...] = (
        "oanda",
        "finnhub",
        "alphavantage",
    )

    DEFAULT_RETRIES = 2

    def __init__(
        self,
        providers: Iterable[str] | None = None,
        *,
        retries: int = DEFAULT_RETRIES,
        retry_delay: float = 0.5,
        cooldown_seconds: float = 30.0,
    ) -> None:
        """
        Initialize ProviderManager.

        Parameters
        ----------
        providers:
            Provider priority order.

        retries:
            Number of retries after the initial request.

            retries=0:
                one total attempt

            retries=2:
                three total attempts

        retry_delay:
            Base delay between retry attempts.

        cooldown_seconds:
            Amount of time a failed provider is temporarily
            excluded from subsequent requests.
        """

        if providers is None:
            providers = self.DEFAULT_PROVIDERS

        normalized_providers = [
            ProviderFactory.normalize_name(name)
            for name in providers
        ]

        if not normalized_providers:
            raise ValueError(
                "At least one provider must be configured."
            )

        # Remove duplicates while preserving priority.
        unique_providers: list[str] = []

        for provider_name in normalized_providers:
            if provider_name not in unique_providers:
                unique_providers.append(
                    provider_name
                )

        for provider_name in unique_providers:
            if not ProviderFactory.is_supported(
                provider_name
            ):
                raise ApplicationError(
                    "Unknown market data provider.",
                    {
                        "provider": provider_name,
                        "available": ProviderFactory.available(),
                    },
                )

        if not isinstance(retries, int):
            raise TypeError(
                "retries must be an integer."
            )

        if isinstance(retries, bool):
            raise TypeError(
                "retries must be an integer."
            )

        if retries < 0:
            raise ValueError(
                "retries cannot be negative."
            )

        if not isinstance(
            retry_delay,
            (int, float),
        ):
            raise TypeError(
                "retry_delay must be a number."
            )

        if retry_delay < 0:
            raise ValueError(
                "retry_delay cannot be negative."
            )

        if not isinstance(
            cooldown_seconds,
            (int, float),
        ):
            raise TypeError(
                "cooldown_seconds must be a number."
            )

        if cooldown_seconds < 0:
            raise ValueError(
                "cooldown_seconds cannot be negative."
            )

        self._providers = tuple(
            unique_providers
        )

        self.retries = retries
        self.retry_delay = float(
            retry_delay
        )
        self.cooldown_seconds = float(
            cooldown_seconds
        )

        self._cooldowns: dict[
            str,
            float,
        ] = {}

        self._last_failures: list[
            ProviderFailure
        ] = []

        self._provider_instances: dict[
            str,
            MarketDataProvider,
        ] = {}

    # ------------------------------------------------------------------
    # Provider configuration
    # ------------------------------------------------------------------

    @property
    def providers(self) -> tuple[str, ...]:
        """
        Return providers in priority order.
        """

        return self._providers

    def set_providers(
        self,
        providers: Iterable[str],
    ) -> None:
        """
        Replace provider priority order.

        Existing provider instances are retained where possible.
        """

        normalized = [
            ProviderFactory.normalize_name(name)
            for name in providers
        ]

        if not normalized:
            raise ValueError(
                "At least one provider must be configured."
            )

        unique: list[str] = []

        for provider_name in normalized:
            if provider_name not in unique:
                unique.append(
                    provider_name
                )

        for provider_name in unique:
            if not ProviderFactory.is_supported(
                provider_name
            ):
                raise ApplicationError(
                    "Unknown market data provider.",
                    {
                        "provider": provider_name,
                        "available": ProviderFactory.available(),
                    },
                )

        self._providers = tuple(
            unique
        )

    # ------------------------------------------------------------------
    # Provider instances
    # ------------------------------------------------------------------

    def _get_provider(
        self,
        provider_name: str,
    ) -> MarketDataProvider:
        """
        Lazily create and cache a provider instance.

        ProviderFactory remains the single creation point.
        """

        normalized_name = (
            ProviderFactory.normalize_name(
                provider_name
            )
        )

        provider = self._provider_instances.get(
            normalized_name
        )

        if provider is None:
            provider = ProviderFactory.create(
                normalized_name
            )

            self._provider_instances[
                normalized_name
            ] = provider

        return provider

    def clear_instances(self) -> None:
        """
        Clear cached provider instances.

        Useful for tests, reconfiguration and recovery.
        """

        self._provider_instances.clear()

    # ------------------------------------------------------------------
    # Cooldown
    # ------------------------------------------------------------------

    def _is_in_cooldown(
        self,
        provider_name: str,
    ) -> bool:
        """
        Return True when the provider is temporarily disabled.
        """

        expires_at = self._cooldowns.get(
            provider_name
        )

        if expires_at is None:
            return False

        if time.monotonic() >= expires_at:
            self._cooldowns.pop(
                provider_name,
                None,
            )
            return False

        return True

    def _put_in_cooldown(
        self,
        provider_name: str,
    ) -> None:
        """
        Temporarily disable a failing provider.
        """

        if self.cooldown_seconds <= 0:
            return

        self._cooldowns[
            provider_name
        ] = (
            time.monotonic()
            + self.cooldown_seconds
        )

    def clear_cooldown(
        self,
        provider_name: str,
    ) -> None:
        """
        Remove a provider from cooldown.
        """

        normalized_name = (
            ProviderFactory.normalize_name(
                provider_name
            )
        )

        self._cooldowns.pop(
            normalized_name,
            None,
        )

    def clear_all_cooldowns(self) -> None:
        """
        Remove all provider cooldowns.
        """

        self._cooldowns.clear()

    # ------------------------------------------------------------------
    # Failure tracking
    # ------------------------------------------------------------------

    @property
    def last_failures(
        self,
    ) -> tuple[ProviderFailure, ...]:
        """
        Return failures from the latest request.
        """

        return tuple(
            self._last_failures
        )

    # ------------------------------------------------------------------
    # Retry logic
    # ------------------------------------------------------------------

    async def _request_with_retry(
        self,
        provider_name: str,
        provider: MarketDataProvider,
        *,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> list[Candle]:
        """
        Execute one provider request with retry logic.
        """

        total_attempts = self.retries + 1

        last_error: Exception | None = None

        for attempt in range(
            1,
            total_attempts + 1,
        ):
            try:
                candles = await provider.get_candles(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=limit,
                )

                return self._validate_result(
                    provider_name=provider_name,
                    candles=candles,
                    symbol=symbol,
                )

            except Exception as error:
                last_error = error

                failure = ProviderFailure(
                    provider=provider_name,
                    attempt=attempt,
                    error_type=type(
                        error
                    ).__name__,
                    message=str(error),
                )

                self._last_failures.append(
                    failure
                )

                logger.warning(
                    "Provider %s failed "
                    "(attempt %d/%d): %s",
                    provider_name,
                    attempt,
                    total_attempts,
                    error,
                )

                if attempt >= total_attempts:
                    break

                if self.retry_delay > 0:
                    # Exponential backoff:
                    #
                    # retry 1 -> delay
                    # retry 2 -> delay * 2
                    # retry 3 -> delay * 4
                    #
                    delay = (
                        self.retry_delay
                        * (
                            2 ** (attempt - 1)
                        )
                    )

                    await asyncio.sleep(
                        delay
                    )

        assert last_error is not None

        raise last_error

    # ------------------------------------------------------------------
    # Result validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_result(
        provider_name: str,
        candles: object,
        symbol: str,
    ) -> list[Candle]:
        """
        Validate the common provider result.

        Provider implementations are responsible for constructing
        Candle objects. The manager verifies the final contract.
        """

        if not isinstance(
            candles,
            list,
        ):
            raise ApplicationError(
                "Provider returned an invalid candle collection.",
                {
                    "provider": provider_name,
                    "symbol": symbol,
                    "expected": "list[Candle]",
                    "actual": type(
                        candles
                    ).__name__,
                },
            )

        for index, candle in enumerate(
            candles
        ):
            if not isinstance(
                candle,
                Candle,
            ):
                raise ApplicationError(
                    "Provider returned an invalid candle.",
                    {
                        "provider": provider_name,
                        "symbol": symbol,
                        "index": index,
                        "expected": "Candle",
                        "actual": type(
                            candle
                        ).__name__,
                    },
                )

        return list(candles)

    # ------------------------------------------------------------------
    # Candle normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_candles(
        candles: list[Candle],
        *,
        limit: int,
    ) -> list[Candle]:
        """
        Final manager-level normalization.

        Guarantees:
        - chronological ordering
        - duplicate timestamp removal
        - maximum requested limit
        """

        unique: dict[
            tuple[str, object],
            Candle,
        ] = {}

        for candle in candles:
            key = (
                candle.symbol,
                candle.timestamp,
            )

            unique[key] = candle

        normalized = sorted(
            unique.values(),
            key=lambda candle: candle.timestamp,
        )

        if len(normalized) > limit:
            normalized = normalized[-limit:]

        return normalized

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
        Fetch candles using the configured provider priority.

        Algorithm
        ---------
        1. Validate basic request.
        2. Iterate through providers in priority order.
        3. Skip providers currently in cooldown.
        4. Create provider lazily.
        5. Retry failed requests.
        6. If a provider fails completely, move to the next.
        7. Validate the returned Candle list.
        8. Normalize ordering and duplicates.
        9. Return the result.

        Raises
        ------
        ApplicationError
            If every usable provider fails.
        """

        if not isinstance(
            symbol,
            str,
        ):
            raise TypeError(
                "symbol must be a string."
            )

        if not symbol.strip():
            raise ValueError(
                "symbol cannot be empty."
            )

        if not isinstance(
            timeframe,
            str,
        ):
            raise TypeError(
                "timeframe must be a string."
            )

        if not timeframe.strip():
            raise ValueError(
                "timeframe cannot be empty."
            )

        if not isinstance(
            limit,
            int,
        ):
            raise TypeError(
                "limit must be an integer."
            )

        if isinstance(
            limit,
            bool,
        ):
            raise TypeError(
                "limit must be an integer."
            )

        if limit < 1:
            raise ValueError(
                "limit must be greater than zero."
            )

        normalized_symbol = (
            symbol.strip().upper()
        )

        normalized_timeframe = (
            timeframe.strip().upper()
        )

        self._last_failures = []

        attempted_providers = 0

        skipped_providers = 0

        for provider_name in self._providers:

            if self._is_in_cooldown(
                provider_name
            ):
                skipped_providers += 1

                logger.info(
                    "Skipping provider %s "
                    "because it is in cooldown.",
                    provider_name,
                )

                continue

            attempted_providers += 1

            try:
                provider = self._get_provider(
                    provider_name
                )

                candles = await self._request_with_retry(
                    provider_name,
                    provider,
                    symbol=normalized_symbol,
                    timeframe=normalized_timeframe,
                    limit=limit,
                )

                candles = self._normalize_candles(
                    candles,
                    limit=limit,
                )

                # A successful provider is immediately
                # removed from cooldown.
                self._cooldowns.pop(
                    provider_name,
                    None,
                )

                logger.info(
                    "Provider %s successfully returned "
                    "%d candles for %s (%s).",
                    provider_name,
                    len(candles),
                    normalized_symbol,
                    normalized_timeframe,
                )

                return candles

            except Exception as error:
                self._put_in_cooldown(
                    provider_name
                )

                logger.warning(
                    "Provider %s exhausted. "
                    "Trying next provider.",
                    provider_name,
                )

                # Continue to the next provider.
                continue

        raise ApplicationError(
            "All market data providers failed.",
            {
                "symbol": normalized_symbol,
                "timeframe": normalized_timeframe,
                "limit": limit,
                "providers": list(
                    self._providers
                ),
                "attempted_providers": attempted_providers,
                "skipped_providers": skipped_providers,
                "failures": [
                    {
                        "provider": failure.provider,
                        "attempt": failure.attempt,
                        "error_type": failure.error_type,
                        "message": failure.message,
                    }
                    for failure
                    in self._last_failures
                ],
            },
        )

    # ------------------------------------------------------------------
    # Provider status
    # ------------------------------------------------------------------

    def status(self) -> dict[str, object]:
        """
        Return a snapshot of manager/provider state.

        No network requests are performed.
        """

        now = time.monotonic()

        cooldowns: dict[str, float] = {}

        for provider_name, expires_at in (
            self._cooldowns.items()
        ):
            remaining = max(
                0.0,
                expires_at - now,
            )

            cooldowns[
                provider_name
            ] = remaining

        return {
            "providers": list(
                self._providers
            ),
            "cached_instances": list(
                self._provider_instances.keys()
            ),
            "cooldowns": cooldowns,
            "retries": self.retries,
            "retry_delay": self.retry_delay,
            "cooldown_seconds": self.cooldown_seconds,
        }


__all__ = [
    "ProviderFailure",
    "ProviderManager",
]

