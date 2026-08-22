
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

    Supports both provider names and directly injected provider
    instances.

    Example:

        ProviderManager(
            providers=[
                "oanda",
                "finnhub",
                "alphavantage",
            ]
        )

    Or:

        ProviderManager(
            providers=[
                custom_provider,
                another_provider,
            ]
        )

    Direct provider instances are especially useful for:
    - tests
    - dependency injection
    - custom providers
    - future provider implementations
    """

    DEFAULT_PROVIDERS: tuple[str, ...] = (
        "oanda",
        "finnhub",
        "alphavantage",
    )

    DEFAULT_RETRIES = 2

    def __init__(
        self,
        providers: (
            Iterable[str | MarketDataProvider]
            | None
        ) = None,
        *,
        retries: int = DEFAULT_RETRIES,
        retry_delay: float = 0.5,
        cooldown_seconds: float = 30.0,
    ) -> None:
        """
        Initialize ProviderManager.

        `providers` may contain either:

            "oanda"

        or an already-created provider instance.

        Provider instances are kept directly and are NOT passed
        through ProviderFactory.
        """

        if providers is None:
            providers = self.DEFAULT_PROVIDERS

        provider_items = list(providers)

        if not provider_items:
            raise ValueError(
                "At least one provider must be configured."
            )

        # --------------------------------------------------------------
        # Retry validation
        # --------------------------------------------------------------

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

        # --------------------------------------------------------------
        # Retry delay validation
        # --------------------------------------------------------------

        if not isinstance(
            retry_delay,
            (int, float),
        ):
            raise TypeError(
                "retry_delay must be a number."
            )

        if isinstance(
            retry_delay,
            bool,
        ):
            raise TypeError(
                "retry_delay must be a number."
            )

        if retry_delay < 0:
            raise ValueError(
                "retry_delay cannot be negative."
            )

        # --------------------------------------------------------------
        # Cooldown validation
        # --------------------------------------------------------------

        if not isinstance(
            cooldown_seconds,
            (int, float),
        ):
            raise TypeError(
                "cooldown_seconds must be a number."
            )

        if isinstance(
            cooldown_seconds,
            bool,
        ):
            raise TypeError(
                "cooldown_seconds must be a number."
            )

        if cooldown_seconds < 0:
            raise ValueError(
                "cooldown_seconds cannot be negative."
            )

        self.retries = retries
        self.retry_delay = float(
            retry_delay
        )
        self.cooldown_seconds = float(
            cooldown_seconds
        )

        # --------------------------------------------------------------
        # Runtime state
        # --------------------------------------------------------------

        self._providers: tuple[str, ...] = ()

        self._provider_instances: dict[
            str,
            MarketDataProvider,
        ] = {}

        self._cooldowns: dict[
            str,
            float,
        ] = {}

        self._last_failures: list[
            ProviderFailure
        ] = []

        # --------------------------------------------------------------
        # Configure providers
        # --------------------------------------------------------------

        self._configure_providers(
            provider_items
        )

    # ==================================================================
    # Provider configuration
    # ==================================================================

    @staticmethod
    def _get_instance_name(
        provider: object,
        index: int,
    ) -> str:
        """
        Determine a stable internal name for an injected provider.

        Priority:

        1. provider.name
        2. provider.provider_name
        3. provider.NAME
        4. class name + index
        """

        for attribute in (
            "name",
            "provider_name",
            "NAME",
        ):
            value = getattr(
                provider,
                attribute,
                None,
            )

            if isinstance(
                value,
                str,
            ) and value.strip():

                try:
                    return (
                        ProviderFactory.normalize_name(
                            value
                        )
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    return value.strip().lower()

        class_name = (
            provider.__class__.__name__
        )

        if class_name:
            return (
                f"{class_name.lower()}_{index}"
            )

        return f"provider_{index}"

    def _configure_providers(
        self,
        providers: list[
            str | MarketDataProvider
        ],
    ) -> None:
        """
        Configure provider priority.

        String names are normalized through ProviderFactory.

        Provider instances are injected directly.
        """

        normalized_providers: list[str] = []

        for index, provider_item in enumerate(
            providers
        ):

            # ----------------------------------------------------------
            # Provider name
            # ----------------------------------------------------------

            if isinstance(
                provider_item,
                str,
            ):

                provider_name = (
                    ProviderFactory.normalize_name(
                        provider_item
                    )
                )

                if not ProviderFactory.is_supported(
                    provider_name
                ):
                    raise ApplicationError(
                        "Unknown market data provider.",
                        {
                            "provider": provider_name,
                            "available": (
                                ProviderFactory.available()
                            ),
                        },
                    )

            # ----------------------------------------------------------
            # Provider instance
            # ----------------------------------------------------------

            else:

                if not hasattr(
                    provider_item,
                    "get_candles",
                ):
                    raise TypeError(
                        "Provider instances must "
                        "implement get_candles()."
                    )

                provider_name = (
                    self._get_instance_name(
                        provider_item,
                        index,
                    )
                )

                # Keep the actual instance.
                self._provider_instances[
                    provider_name
                ] = provider_item

            # ----------------------------------------------------------
            # Preserve priority and remove duplicates.
            # ----------------------------------------------------------

            if (
                provider_name
                not in normalized_providers
            ):
                normalized_providers.append(
                    provider_name
                )

        if not normalized_providers:
            raise ValueError(
                "At least one provider must be configured."
            )

        self._providers = tuple(
            normalized_providers
        )

    # ==================================================================
    # Public provider configuration API
    # ==================================================================

    @property
    def providers(
        self,
    ) -> tuple[str, ...]:
        """
        Return configured providers in priority order.
        """

        return self._providers

    def set_providers(
        self,
        providers: Iterable[
            str | MarketDataProvider
        ],
    ) -> None:
        """
        Replace provider priority.

        Both provider names and provider instances are supported.
        """

        provider_items = list(providers)

        if not provider_items:
            raise ValueError(
                "At least one provider must be configured."
            )

        old_providers = self._providers
        old_instances = (
            self._provider_instances.copy()
        )

        self._provider_instances.clear()

        try:
            self._configure_providers(
                provider_items
            )

        except Exception:
            self._providers = old_providers
            self._provider_instances = (
                old_instances
            )
            raise

    # ==================================================================
    # Provider instances
    # ==================================================================

    def _get_provider(
        self,
        provider_name: str,
    ) -> MarketDataProvider:
        """
        Return a cached provider instance.

        Injected provider instances are returned directly.

        Provider names are created lazily through ProviderFactory.
        """

        normalized_name = (
            ProviderFactory.normalize_name(
                provider_name
            )
        )

        provider = (
            self._provider_instances.get(
                normalized_name
            )
        )

        if provider is not None:
            return provider

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
        """

        self._provider_instances.clear()

    # ==================================================================
    # Cooldown
    # ==================================================================

    def _is_in_cooldown(
        self,
        provider_name: str,
    ) -> bool:
        """
        Return True if provider is currently in cooldown.
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
        Put provider into temporary cooldown.
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
        Remove one provider from cooldown.
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

    def clear_all_cooldowns(
        self,
    ) -> None:
        """
        Remove all provider cooldowns.
        """

        self._cooldowns.clear()

    # ==================================================================
    # Failure tracking
    # ==================================================================

    @property
    def last_failures(
        self,
    ) -> tuple[ProviderFailure, ...]:
        """
        Return failures recorded during the latest request.
        """

        return tuple(
            self._last_failures
        )

    # ==================================================================
    # Retry logic
    # ==================================================================

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
        Execute provider request with retry and exponential backoff.
        """

        total_attempts = (
            self.retries + 1
        )

        last_error: Exception | None = None

        for attempt in range(
            1,
            total_attempts + 1,
        ):

            try:

                candles = (
                    await provider.get_candles(
                        symbol=symbol,
                        timeframe=timeframe,
                        limit=limit,
                    )
                )

                return self._validate_result(
                    provider_name=provider_name,
                    candles=candles,
                    symbol=symbol,
                )

            except Exception as error:

                last_error = error

                self._last_failures.append(
                    ProviderFailure(
                        provider=provider_name,
                        attempt=attempt,
                        error_type=type(
                            error
                        ).__name__,
                        message=str(error),
                    )
                )

                logger.warning(
                    "Provider %s failed "
                    "(attempt %d/%d): %s",
                    provider_name,
                    attempt,
                    total_attempts,
                    error,
                )

                if (
                    attempt
                    >= total_attempts
                ):
                    break

                if self.retry_delay > 0:

                    delay = (
                        self.retry_delay
                        * (
                            2
                            ** (
                                attempt - 1
                            )
                        )
                    )

                    await asyncio.sleep(
                        delay
                    )

        assert last_error is not None

        raise last_error

    # ==================================================================
    # Result validation
    # ==================================================================

    @staticmethod
    def _validate_result(
        provider_name: str,
        candles: object,
        symbol: str,
    ) -> list[Candle]:
        """
        Validate provider output.
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

    # ==================================================================
    # Candle normalization
    # ==================================================================

    @staticmethod
    def _normalize_candles(
        candles: list[Candle],
        *,
        limit: int,
    ) -> list[Candle]:
        """
        Normalize final candle data.

        Guarantees:

        - chronological order
        - duplicate timestamp removal
        - requested limit
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
            key=lambda candle:
                candle.timestamp,
        )

        if len(normalized) > limit:
            normalized = normalized[-limit:]

        return normalized

    # ==================================================================
    # Main public API
    # ==================================================================

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[Candle]:
        """
        Fetch candles using provider priority.

        Flow:

        1. Validate request.
        2. Iterate providers.
        3. Skip providers in cooldown.
        4. Obtain provider instance.
        5. Retry failed requests.
        6. Fall back to next provider.
        7. Validate candles.
        8. Normalize candles.
        9. Return result.
        """

        # --------------------------------------------------------------
        # Symbol
        # --------------------------------------------------------------

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

        # --------------------------------------------------------------
        # Timeframe
        # --------------------------------------------------------------

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

        # --------------------------------------------------------------
        # Limit
        # --------------------------------------------------------------

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

        # Reset failures for this request.
        self._last_failures = []

        attempted_providers = 0
        skipped_providers = 0

        # --------------------------------------------------------------
        # Provider priority loop
        # --------------------------------------------------------------

        for provider_name in self._providers:

            # ----------------------------------------------------------
            # Cooldown
            # ----------------------------------------------------------

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

                # ------------------------------------------------------
                # Obtain provider
                # ------------------------------------------------------

                provider = self._get_provider(
                    provider_name
                )

                # ------------------------------------------------------
                # Request with retry
                # ------------------------------------------------------

                candles = (
                    await self._request_with_retry(
                        provider_name,
                        provider,
                        symbol=normalized_symbol,
                        timeframe=(
                            normalized_timeframe
                        ),
                        limit=limit,
                    )
                )

                # ------------------------------------------------------
                # Final normalization
                # ------------------------------------------------------

                candles = (
                    self._normalize_candles(
                        candles,
                        limit=limit,
                    )
                )

                # Successful provider:
                # remove cooldown.
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

                # ------------------------------------------------------
                # Provider completely failed.
                # Move to next provider.
                # ------------------------------------------------------

                self._put_in_cooldown(
                    provider_name
                )

                logger.warning(
                    "Provider %s exhausted. "
                    "Trying next provider: %s",
                    provider_name,
                    error,
                )

                continue

        # --------------------------------------------------------------
        # All providers failed
        # --------------------------------------------------------------

        raise ApplicationError(
            "All market data providers failed.",
            {
                "symbol": normalized_symbol,
                "timeframe": normalized_timeframe,
                "limit": limit,
                "providers": list(
                    self._providers
                ),
                "attempted_providers": (
                    attempted_providers
                ),
                "skipped_providers": (
                    skipped_providers
                ),
                "failures": [
                    {
                        "provider": (
                            failure.provider
                        ),
                        "attempt": (
                            failure.attempt
                        ),
                        "error_type": (
                            failure.error_type
                        ),
                        "message": (
                            failure.message
                        ),
                    }
                    for failure in (
                        self._last_failures
                    )
                ],
            },
        )

    # ==================================================================
    # Status
    # ==================================================================

    def status(
        self,
    ) -> dict[str, object]:
        """
        Return current manager state.

        No network request is performed.
        """

        now = time.monotonic()

        cooldowns: dict[
            str,
            float,
        ] = {}

        for (
            provider_name,
            expires_at,
        ) in self._cooldowns.items():

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
            "cooldown_seconds": (
                self.cooldown_seconds
            ),
        }


__all__ = [
    "ProviderFailure",
    "ProviderManager",
]

