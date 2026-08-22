
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


ProviderReference = str | MarketDataProvider


class ProviderManager:
    """
    High-level manager for market-data providers.

    Responsibilities
    ----------------
    - Manage provider priority.
    - Create providers through ProviderFactory.
    - Accept both provider names and already-created provider instances.
    - Retry temporary provider failures.
    - Fall back to the next provider.
    - Keep provider failures isolated.
    - Validate the final candle result.
    - Normalize candle ordering and duplicates.
    - Preserve the common MarketDataProvider contract.

    Provider names:
        "oanda"
        "finnhub"
        "alphavantage"

    Provider instances:
        Any object implementing the required get_candles() contract.

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
        providers: Iterable[ProviderReference] | None = None,
        *,
        retries: int = DEFAULT_RETRIES,
        retry_delay: float = 0.5,
        cooldown_seconds: float = 30.0,
    ) -> None:
        """
        Initialize ProviderManager.

        providers may contain either:

            - provider names
            - provider instances

        Example:

            ProviderManager(
                providers=[
                    "oanda",
                    "finnhub",
                ]
            )

        or:

            ProviderManager(
                providers=[
                    fake_provider,
                    another_provider,
                ]
            )
        """

        if providers is None:
            providers = self.DEFAULT_PROVIDERS

        raw_providers = list(providers)

        if not raw_providers:
            raise ValueError(
                "At least one provider must be configured."
            )

        self.retries = self._validate_non_negative_int(
            retries,
            "retries",
        )

        self.retry_delay = self._validate_non_negative_number(
            retry_delay,
            "retry_delay",
        )

        self.cooldown_seconds = self._validate_non_negative_number(
            cooldown_seconds,
            "cooldown_seconds",
        )

        self._providers: tuple[str, ...]
        self._provider_instances: dict[
            str,
            MarketDataProvider,
        ] = {}

        self._provider_objects: dict[
            str,
            MarketDataProvider,
        ] = {}

        provider_names: list[str] = []

        for index, provider_reference in enumerate(
            raw_providers
        ):
            if isinstance(
                provider_reference,
                str,
            ):
                provider_name = (
                    ProviderFactory.normalize_name(
                        provider_reference
                    )
                )

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

                canonical_name = provider_name
                provider_instance = None

            else:
                provider_instance = provider_reference

                if not self._is_provider_instance(
                    provider_instance
                ):
                    raise TypeError(
                        "Each provider must be either "
                        "a provider name string or an object "
                        "implementing get_candles(). "
                        f"Invalid provider at index {index}: "
                        f"{type(provider_reference).__name__}"
                    )

                canonical_name = (
                    self._provider_instance_name(
                        provider_instance,
                        index,
                    )
                )

            if canonical_name in provider_names:
                continue

            provider_names.append(
                canonical_name
            )

            if provider_instance is not None:
                self._provider_objects[
                    canonical_name
                ] = provider_instance

        self._providers = tuple(
            provider_names
        )

        if not self._providers:
            raise ValueError(
                "At least one provider must be configured."
            )

        self._cooldowns: dict[
            str,
            float,
        ] = {}

        self._last_failures: list[
            ProviderFailure
        ] = []

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_non_negative_int(
        value: int,
        name: str,
    ) -> int:
        if isinstance(value, bool):
            raise TypeError(
                f"{name} must be an integer."
            )

        if not isinstance(value, int):
            raise TypeError(
                f"{name} must be an integer."
            )

        if value < 0:
            raise ValueError(
                f"{name} cannot be negative."
            )

        return value

    @staticmethod
    def _validate_non_negative_number(
        value: float,
        name: str,
    ) -> float:
        if isinstance(value, bool):
            raise TypeError(
                f"{name} must be a number."
            )

        if not isinstance(
            value,
            (int, float),
        ):
            raise TypeError(
                f"{name} must be a number."
            )

        if value < 0:
            raise ValueError(
                f"{name} cannot be negative."
            )

        return float(value)

    @staticmethod
    def _is_provider_instance(
        provider: object,
    ) -> bool:
        """
        Determine whether an object provides the common
        get_candles() interface.

        We intentionally use duck typing here so lightweight
        test doubles such as FakeProvider can be used without
        inheriting from MarketDataProvider.
        """

        return callable(
            getattr(
                provider,
                "get_candles",
                None,
            )
        )

    @staticmethod
    def _provider_instance_name(
        provider: MarketDataProvider,
        index: int,
    ) -> str:
        """
        Resolve a stable canonical name for an injected provider
        instance.

        Real MarketDataProvider implementations expose `name`.

        Lightweight test doubles may not, so we generate a stable
        local name such as:

            fakeprovider_0
            fakeprovider_1
        """

        name = getattr(
            provider,
            "name",
            None,
        )

        if isinstance(
            name,
            str,
        ) and name.strip():
            try:
                return ProviderFactory.normalize_name(
                    name
                )
            except (
                TypeError,
                ValueError,
            ):
                pass

        provider_name = getattr(
            provider,
            "provider_name",
            None,
        )

        if isinstance(
            provider_name,
            str,
        ) and provider_name.strip():
            try:
                return ProviderFactory.normalize_name(
                    provider_name
                )
            except (
                TypeError,
                ValueError,
            ):
                pass

        class_name = (
            provider.__class__.__name__
        )

        normalized = (
            class_name.strip()
            .lower()
        )

        if normalized.endswith(
            "provider"
        ):
            normalized = normalized[
                :-len("provider")
            ]

        if not normalized:
            normalized = "provider"

        return f"{normalized}_{index}"

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
        providers: Iterable[ProviderReference],
    ) -> None:
        """
        Replace provider priority order.

        Existing provider instances are retained where possible.
        """

        raw_providers = list(providers)

        if not raw_providers:
            raise ValueError(
                "At least one provider must be configured."
            )

        normalized: list[str] = []
        new_objects: dict[
            str,
            MarketDataProvider,
        ] = {}

        for index, provider_reference in enumerate(
            raw_providers
        ):
            if isinstance(
                provider_reference,
                str,
            ):
                provider_name = (
                    ProviderFactory.normalize_name(
                        provider_reference
                    )
                )

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

                canonical_name = provider_name

            else:
                if not self._is_provider_instance(
                    provider_reference
                ):
                    raise TypeError(
                        "Each provider must be either "
                        "a provider name string or an object "
                        "implementing get_candles()."
                    )

                canonical_name = (
                    self._provider_instance_name(
                        provider_reference,
                        index,
                    )
                )

                new_objects[
                    canonical_name
                ] = provider_reference

            if canonical_name not in normalized:
                normalized.append(
                    canonical_name
                )

        self._providers = tuple(
            normalized
        )

        self._provider_objects.update(
            new_objects
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

        Injected provider instances always take precedence over
        ProviderFactory creation.
        """

        normalized_name = (
            ProviderFactory.normalize_name(
                provider_name
            )
            if provider_name in self._provider_objects
            else provider_name
        )

        injected = self._provider_objects.get(
            normalized_name
        )

        if injected is not None:
            return injected

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
        Clear cached factory-created provider instances.

        Injected provider instances are intentionally retained.
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

        For injected providers, the generated canonical name can
        be used as returned by `providers`.
        """

        if provider_name in self._cooldowns:
            self._cooldowns.pop(
                provider_name,
                None,
            )
            return

        try:
            normalized_name = (
                ProviderFactory.normalize_name(
                    provider_name
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            normalized_name = provider_name

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

        Important behavior:

        - Exceptions trigger retries.
        - Invalid results trigger retries.
        - An empty list is treated as an unsuccessful provider
          response when other providers are available.
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
                candles = await provider.get_candles(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=limit,
                )

                validated = self._validate_result(
                    provider_name=provider_name,
                    candles=candles,
                    symbol=symbol,
                )

                if not validated:
                    raise ApplicationError(
                        "Provider returned no candles.",
                        {
                            "provider": provider_name,
                            "symbol": symbol,
                            "timeframe": timeframe,
                        },
                    )

                return validated

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
                    delay = (
                        self.retry_delay
                        * (
                            2 ** (
                                attempt - 1
                            )
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
                    "Provider returned invalid candle data.",
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
            normalized = normalized[
                -limit:
            ]

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
        Fetch candles using configured provider priority.

        Algorithm
        ---------
        1. Validate basic request.
        2. Iterate through providers in priority order.
        3. Skip providers currently in cooldown.
        4. Create or use the injected provider.
        5. Retry failed requests.
        6. Empty responses are treated as provider failures.
        7. Fall back to the next provider.
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

        if isinstance(
            limit,
            bool,
        ):
            raise TypeError(
                "limit must be an integer."
            )

        if not isinstance(
            limit,
            int,
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

                # A provider returning no usable candles is not
                # considered successful.
                if not candles:
                    raise ApplicationError(
                        "Provider returned no usable candles.",
                        {
                            "provider": provider_name,
                            "symbol": normalized_symbol,
                            "timeframe": normalized_timeframe,
                        },
                    )

                # Successful provider is removed from cooldown.
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

    def status(
        self,
    ) -> dict[str, object]:
        """
        Return a snapshot of manager/provider state.

        No network requests are performed.
        """

        now = time.monotonic()

        cooldowns: dict[str, float] = {}

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
            "injected_instances": list(
                self._provider_objects.keys()
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
