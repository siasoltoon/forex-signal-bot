# =========================
# PART 1/4
# data/provider_manager.py
# FINAL v3
# =========================

from __future__ import annotations

import asyncio
import math
import time

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


from core.errors import ApplicationError
from core.logger import setup_logger

from data.base import MarketDataProvider
from data.factory import ProviderFactory
from data.models import Candle


logger = setup_logger()


# ==========================================================
# Provider Exceptions
# ==========================================================


class ProviderError(Exception):
    """Base provider exception."""


class ProviderRateLimitError(ProviderError):
    """Provider rate limit exceeded."""


class ProviderTemporaryUnavailableError(ProviderError):
    """Provider temporarily unavailable."""


class ProviderAuthenticationError(ProviderError):
    """Provider authentication failed."""


class ProviderInvalidDataError(ProviderError):
    """Provider returned invalid data."""


class ProviderTimeoutError(ProviderError):
    """Provider timeout."""


# ==========================================================
# Circuit Breaker
# ==========================================================


class CircuitState(str, Enum):

    CLOSED = "closed"

    OPEN = "open"

    HALF_OPEN = "half_open"


# ==========================================================
# Data Models
# ==========================================================


@dataclass(
    frozen=True,
    slots=True,
)
class ProviderFailure:

    provider: str

    attempt: int

    error_type: str

    message: str



@dataclass(slots=True)
class ProviderHealth:

    provider: str

    status: str = "healthy"

    circuit_state: str = CircuitState.CLOSED.value

    total_requests: int = 0

    total_attempts: int = 0

    successful_requests: int = 0

    failed_requests: int = 0

    consecutive_failures: int = 0

    last_success_time: float | None = None

    last_failure_time: float | None = None

    last_error_type: str | None = None

    last_error_message: str | None = None

    cooldown_until: float | None = None

    opened_at: float | None = None

    half_open_test: bool = False



@dataclass(slots=True)
class ProviderMetrics:

    provider: str

    total_requests: int = 0

    total_attempts: int = 0

    successful_requests: int = 0

    failed_requests: int = 0

    total_latency: float = 0.0


    @property
    def average_latency(
        self,
    ) -> float:

        if self.total_attempts == 0:

            return 0.0

        return (
            self.total_latency
            /
            self.total_attempts
        )


    @property
    def success_rate(
        self,
    ) -> float:

        if self.total_requests == 0:

            return 0.0

        return (
            self.successful_requests
            /
            self.total_requests
        )



ProviderReference = (
    str
    |
    MarketDataProvider
)



# ==========================================================
# Provider Manager
# ==========================================================


class ProviderManager:

    """
    Production market data provider manager.

    Features:

    - Provider priority
    - Factory integration
    - Dependency injection
    - Retry system
    - Timeout handling
    - Failover
    - Circuit breaker
    - Health monitoring
    - Metrics
    - Validation
    - Normalization
    """



    DEFAULT_PROVIDERS = (
        "oanda",
        "finnhub",
        "alphavantage",
    )


    DEFAULT_RETRIES = 2

    DEFAULT_TIMEOUT = 15.0

    DEFAULT_COOLDOWN = 30.0

    DEFAULT_FAILURE_THRESHOLD = 3



    def __init__(
        self,
        providers: Iterable[ProviderReference] | None = None,
        *,
        retries: int = DEFAULT_RETRIES,
        timeout: float = DEFAULT_TIMEOUT,
        retry_delay: float = 0.5,
        cooldown_seconds: float = DEFAULT_COOLDOWN,
        failure_threshold: int = DEFAULT_FAILURE_THRESHOLD,
    ) -> None:


        if providers is None:

            providers = self.DEFAULT_PROVIDERS



        raw_providers = list(
            providers
        )


        if not raw_providers:

            raise ValueError(
                "At least one provider required."
            )



        self.retries = self._validate_int(
            retries,
            "retries",
        )


        self.timeout = self._validate_number(
            timeout,
            "timeout",
        )


        self.retry_delay = self._validate_number(
            retry_delay,
            "retry_delay",
        )


        self.cooldown_seconds = self._validate_number(
            cooldown_seconds,
            "cooldown_seconds",
        )


        self.failure_threshold = self._validate_int(
            failure_threshold,
            "failure_threshold",
        )



        self._state_lock = asyncio.Lock()



        self._providers: tuple[str, ...]


        self._provider_instances: dict[
            str,
            MarketDataProvider,
        ] = {}


        self._provider_objects: dict[
            str,
            MarketDataProvider,
        ] = {}



        names: list[str] = []



        for index, reference in enumerate(
            raw_providers
        ):


            if isinstance(
                reference,
                str,
            ):

                name = ProviderFactory.normalize_name(
                    reference
                )


                if not ProviderFactory.is_supported(
                    name
                ):

                    raise ApplicationError(
                        "Unknown provider.",
                        {
                            "provider": name,
                            "available": ProviderFactory.available(),
                        },
                    )


                instance = None



            else:

                instance = reference


                if not self._is_provider_instance(
                    instance
                ):

                    raise TypeError(
                        "Invalid provider instance."
                    )


                name = self._provider_instance_name(
                    instance,
                    index,
                )



            if name in names:

                continue


            names.append(
                name
            )


            if instance is not None:

                self._provider_objects[
                    name
                ] = instance



        self._providers = tuple(
            names
        )



        if not self._providers:

            raise ValueError(
                "No providers configured."
            )



        self._provider_health = {
            name: ProviderHealth(
                provider=name
            )
            for name in self._providers
        }


        self._metrics = {
            name: ProviderMetrics(
                provider=name
            )
            for name in self._providers
        }


        self._cooldowns: dict[
            str,
            float,
        ] = {}


        self._last_failures: list[
            ProviderFailure
        ] = []

# =========================
# PART 2/4
# data/provider_manager.py
# FINAL v3
# =========================


    # ======================================================
    # Validation Helpers
    # ======================================================


    @staticmethod
    def _validate_int(
        value: int,
        name: str,
    ) -> int:


        if isinstance(
            value,
            bool,
        ):

            raise TypeError(
                f"{name} must be integer."
            )


        if not isinstance(
            value,
            int,
        ):

            raise TypeError(
                f"{name} must be integer."
            )


        if value < 0:

            raise ValueError(
                f"{name} cannot be negative."
            )


        return value





    @staticmethod
    def _validate_number(
        value: float,
        name: str,
    ) -> float:


        if isinstance(
            value,
            bool,
        ):

            raise TypeError(
                f"{name} must be number."
            )


        if not isinstance(
            value,
            (int, float),
        ):

            raise TypeError(
                f"{name} must be number."
            )


        if not math.isfinite(
            value
        ):

            raise ValueError(
                f"{name} must be finite."
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


        for attribute in (
            "name",
            "provider_name",
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

                return ProviderFactory.normalize_name(
                    value
                )



        class_name = (
            provider.__class__.__name__
            .lower()
        )


        if class_name.endswith(
            "provider"
        ):

            class_name = (
                class_name[:-8]
            )


        return (
            f"{class_name or 'provider'}_{index}"
        )





    # ======================================================
    # Provider Access
    # ======================================================


    @property
    def providers(
        self,
    ) -> tuple[str, ...]:

        return self._providers





    def _get_provider(
        self,
        provider_name: str,
    ) -> MarketDataProvider:


        injected = (
            self._provider_objects
            .get(
                provider_name
            )
        )


        if injected is not None:

            return injected



        cached = (
            self._provider_instances
            .get(
                provider_name
            )
        )


        if cached is not None:

            return cached



        try:

            provider = ProviderFactory.create(
                provider_name
            )


        except Exception as error:

            raise ProviderTemporaryUnavailableError(
                f"Cannot create provider {provider_name}: {error}"
            )



        self._provider_instances[
            provider_name
        ] = provider



        return provider





    def clear_instances(
        self,
    ) -> None:

        self._provider_instances.clear()





    # ======================================================
    # State Access
    # ======================================================


    def _get_health(
        self,
        provider_name: str,
    ) -> ProviderHealth:


        if provider_name not in self._provider_health:

            self._provider_health[
                provider_name
            ] = ProviderHealth(
                provider=provider_name
            )


        return self._provider_health[
            provider_name
        ]





    def _get_metrics(
        self,
        provider_name: str,
    ) -> ProviderMetrics:


        if provider_name not in self._metrics:

            self._metrics[
                provider_name
            ] = ProviderMetrics(
                provider=provider_name
            )


        return self._metrics[
            provider_name
        ]





    def _register_attempt(
        self,
        provider_name: str,
    ) -> float:


        health = self._get_health(
            provider_name
        )


        metrics = self._get_metrics(
            provider_name
        )


        health.total_attempts += 1

        metrics.total_attempts += 1


        return time.monotonic()





    def _mark_success(
        self,
        provider_name: str,
        latency: float,
    ) -> None:


        health = self._get_health(
            provider_name
        )


        metrics = self._get_metrics(
            provider_name
        )


        health.total_requests += 1

        health.successful_requests += 1

        health.consecutive_failures = 0

        health.status = "healthy"

        health.circuit_state = (
            CircuitState.CLOSED.value
        )

        health.half_open_test = False

        health.last_success_time = (
            time.time()
        )

        health.last_error_type = None

        health.last_error_message = None


        metrics.total_requests += 1

        metrics.successful_requests += 1

        metrics.total_latency += latency


        self.clear_cooldown(
            provider_name
        )





    def _mark_failure(
        self,
        provider_name: str,
        error: Exception,
        latency: float,
    ) -> None:


        health = self._get_health(
            provider_name
        )


        metrics = self._get_metrics(
            provider_name
        )


        health.total_requests += 1

        health.failed_requests += 1

        health.consecutive_failures += 1

        health.last_failure_time = (
            time.time()
        )

        health.last_error_type = (
            type(error).__name__
        )

        health.last_error_message = (
            str(error)
        )


        metrics.total_requests += 1

        metrics.failed_requests += 1

        metrics.total_latency += latency



        if (
            health.consecutive_failures
            >= self.failure_threshold
        ):

            health.circuit_state = (
                CircuitState.OPEN.value
            )

            health.opened_at = (
                time.time()
            )



        if isinstance(
            error,
            ProviderRateLimitError,
        ):

            health.status = "rate_limited"


        elif isinstance(
            error,
            ProviderAuthenticationError,
        ):

            health.status = "authentication_error"


        elif isinstance(
            error,
            ProviderTimeoutError,
        ):

            health.status = "timeout"


        elif isinstance(
            error,
            ProviderTemporaryUnavailableError,
        ):

            health.status = "unavailable"


        elif isinstance(
            error,
            ProviderInvalidDataError,
        ):

            health.status = "invalid_data"


        else:

            health.status = "degraded"





    # ======================================================
    # Error Classification
    # ======================================================


    @staticmethod
    def _classify_error(
        error: Exception,
    ) -> Exception:


        if isinstance(
            error,
            ProviderError,
        ):

            return error



        message = str(
            error
        ).lower()



        if any(
            item in message
            for item in (
                "429",
                "rate limit",
                "too many requests",
                "quota",
            )
        ):

            return ProviderRateLimitError(
                str(error)
            )



        if any(
            item in message
            for item in (
                "timeout",
                "timed out",
                "connection",
                "502",
                "503",
                "504",
                "temporarily unavailable",
            )
        ):

            return ProviderTemporaryUnavailableError(
                str(error)
            )



        if any(
            item in message
            for item in (
                "401",
                "403",
                "api key",
                "unauthorized",
                "authentication",
            )
        ):

            return ProviderAuthenticationError(
                str(error)
            )



        if any(
            item in message
            for item in (
                "invalid",
                "malformed",
                "missing candle",
                "empty data",
            )
        ):

            return ProviderInvalidDataError(
                str(error)
            )



        return error

# =========================
# PART 3/4
# data/provider_manager.py
# FINAL v3
# =========================


    # ======================================================
    # Circuit Breaker + Cooldown
    # ======================================================


    def _is_in_cooldown(
        self,
        provider_name: str,
    ) -> bool:


        expires = (
            self._cooldowns.get(
                provider_name
            )
        )


        if expires is None:

            return False



        if time.monotonic() >= expires:


            self.clear_cooldown(
                provider_name
            )


            health = self._get_health(
                provider_name
            )


            if (
                health.circuit_state
                ==
                CircuitState.OPEN.value
            ):

                health.circuit_state = (
                    CircuitState.HALF_OPEN.value
                )


                health.half_open_test = False



            return False



        return True





    def _put_in_cooldown(
        self,
        provider_name: str,
        error: Exception,
    ) -> None:


        health = self._get_health(
            provider_name
        )


        if self.cooldown_seconds <= 0:

            return



        multiplier = 1



        if isinstance(
            error,
            ProviderRateLimitError,
        ):

            multiplier = 5



        elif isinstance(
            error,
            ProviderAuthenticationError,
        ):

            multiplier = 10



        elif isinstance(
            error,
            ProviderTemporaryUnavailableError,
        ):

            multiplier = 2



        multiplier *= min(
            max(
                health.consecutive_failures,
                1,
            ),
            10,
        )



        expires = (
            time.monotonic()
            +
            (
                self.cooldown_seconds
                *
                multiplier
            )
        )



        self._cooldowns[
            provider_name
        ] = expires



        health.cooldown_until = expires





    def clear_cooldown(
        self,
        provider_name: str,
    ) -> None:


        self._cooldowns.pop(
            provider_name,
            None,
        )


        health = self._provider_health.get(
            provider_name
        )


        if health:

            health.cooldown_until = None





    def _is_provider_available(
        self,
        provider_name: str,
    ) -> bool:


        health = self._get_health(
            provider_name
        )


        if self._is_in_cooldown(
            provider_name
        ):

            return False



        if (
            health.circuit_state
            ==
            CircuitState.OPEN.value
        ):

            return False



        if (
            health.circuit_state
            ==
            CircuitState.HALF_OPEN.value
        ):


            if health.half_open_test:

                return False


            health.half_open_test = True



        return True





    # ======================================================
    # Retry Engine
    # ======================================================


    async def _request_with_retry(
        self,
        provider_name: str,
        provider: MarketDataProvider,
        *,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> list[Candle]:


        attempts = (
            self.retries + 1
        )


        last_error: Exception | None = None



        for attempt in range(
            1,
            attempts + 1,
        ):


            start = self._register_attempt(
                provider_name
            )


            try:


                candles = await asyncio.wait_for(
                    provider.get_candles(
                        symbol=symbol,
                        timeframe=timeframe,
                        limit=limit,
                    ),
                    timeout=self.timeout,
                )



                validated = (
                    self._validate_result(
                        provider_name,
                        candles,
                    )
                )



                if not validated:

                    raise ProviderInvalidDataError(
                        "Provider returned empty candle data."
                    )



                latency = (
                    time.monotonic()
                    -
                    start
                )


                self._mark_success(
                    provider_name,
                    latency,
                )


                return validated



            except asyncio.TimeoutError:


                error = ProviderTimeoutError(
                    f"{provider_name} request timeout."
                )


                last_error = error



                latency = (
                    time.monotonic()
                    -
                    start
                )


                self._mark_failure(
                    provider_name,
                    error,
                    latency,
                )


                self._record_failure(
                    provider_name,
                    attempt,
                    error,
                )



            except Exception as error:


                classified = (
                    self._classify_error(
                        error
                    )
                )


                last_error = classified



                latency = (
                    time.monotonic()
                    -
                    start
                )


                self._mark_failure(
                    provider_name,
                    classified,
                    latency,
                )


                self._record_failure(
                    provider_name,
                    attempt,
                    classified,
                )



            if attempt < attempts:


                await asyncio.sleep(
                    self.retry_delay
                    *
                    (
                        2 **
                        (
                            attempt - 1
                        )
                    )
                )



        assert last_error is not None


        raise last_error





    def _record_failure(
        self,
        provider_name: str,
        attempt: int,
        error: Exception,
    ) -> None:


        self._last_failures.append(
            ProviderFailure(
                provider=provider_name,
                attempt=attempt,
                error_type=type(
                    error
                ).__name__,
                message=str(
                    error
                ),
            )
        )


        logger.warning(
            "Provider %s attempt %s failed: %s",
            provider_name,
            attempt,
            error,
        )





    # ======================================================
    # Candle Validation
    # ======================================================


    @staticmethod
    def _validate_result(
        provider_name: str,
        candles: object,
    ) -> list[Candle]:


        if isinstance(
            candles,
            (str, bytes),
        ):

            raise ProviderInvalidDataError(
                f"{provider_name} returned invalid candle type."
            )



        if not isinstance(
            candles,
            list,
        ):

            raise ProviderInvalidDataError(
                f"{provider_name} returned invalid candle container."
            )



        result: list[Candle] = []



        for candle in candles:


            if not isinstance(
                candle,
                Candle,
            ):

                raise ProviderInvalidDataError(
                    f"{provider_name} returned invalid candle object."
                )


            result.append(
                candle
            )



        return result





    # ======================================================
    # Candle Normalization
    # ======================================================


    @staticmethod
    def _normalize_candles(
        candles: list[Candle],
        *,
        limit: int,
    ) -> list[Candle]:


        unique: dict[
            tuple[object, object],
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
            key=lambda item: item.timestamp,
        )



        if len(normalized) > limit:

            normalized = normalized[
                -limit:
            ]



        return normalized

# =========================
# PART 4/4
# data/provider_manager.py
# FINAL v3
# =========================


    # ======================================================
    # Public Market Data API
    # ======================================================


    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[Candle]:


        if not isinstance(
            symbol,
            str,
        ):

            raise TypeError(
                "symbol must be string."
            )


        if not isinstance(
            timeframe,
            str,
        ):

            raise TypeError(
                "timeframe must be string."
            )


        if not isinstance(
            limit,
            int,
        ):

            raise TypeError(
                "limit must be integer."
            )


        if limit <= 0:

            raise ValueError(
                "limit must be positive."
            )



        symbol = (
            symbol.strip()
            .upper()
        )


        timeframe = (
            timeframe.strip()
            .upper()
        )



        self._last_failures.clear()



        attempted = 0

        skipped = 0



        for provider_name in self._providers:


            if not self._is_provider_available(
                provider_name
            ):

                skipped += 1

                continue



            attempted += 1



            try:


                provider = self._get_provider(
                    provider_name
                )



                candles = await self._request_with_retry(
                    provider_name,
                    provider,
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=limit,
                )



                normalized = self._normalize_candles(
                    candles,
                    limit=limit,
                )



                if not normalized:

                    raise ProviderInvalidDataError(
                        "No usable candles after normalization."
                    )



                return normalized



            except Exception as error:


                logger.warning(
                    "Provider %s failed. Switching provider.",
                    provider_name,
                )


                self._put_in_cooldown(
                    provider_name,
                    error,
                )



        raise ApplicationError(
            "All market data providers failed.",
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "limit": limit,
                "attempted": attempted,
                "skipped": skipped,
                "failures": [
                    {
                        "provider": item.provider,
                        "attempt": item.attempt,
                        "error_type": item.error_type,
                        "message": item.message,
                    }
                    for item
                    in self._last_failures
                ],
            },
        )





    # ======================================================
    # Status API
    # ======================================================


    @staticmethod
    def _snapshot(
        obj,
    ) -> dict[str, object]:


        return {
            key: getattr(
                obj,
                key,
            )
            for key
            in obj.__dataclass_fields__
        }





    def get_provider_health(
        self,
        provider_name: str,
    ) -> dict[str, object]:


        return self._snapshot(
            self._get_health(
                provider_name
            )
        )





    def get_all_provider_health(
        self,
    ) -> dict[str, dict[str, object]]:


        return {
            name: self._snapshot(
                health
            )
            for name, health
            in self._provider_health.items()
        }





    def status(
        self,
    ) -> dict[str, object]:


        now = time.monotonic()



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


            "cooldowns": {

                name: max(
                    0,
                    expires - now,
                )

                for name, expires
                in self._cooldowns.items()
            },


            "health": (
                self.get_all_provider_health()
            ),


            "metrics": {

                name: self._snapshot(
                    metric
                )

                for name, metric
                in self._metrics.items()

            },


            "configuration": {

                "retries": self.retries,

                "timeout": self.timeout,

                "retry_delay": self.retry_delay,

                "cooldown_seconds": (
                    self.cooldown_seconds
                ),

                "failure_threshold": (
                    self.failure_threshold
                ),

            },

        }





    @property
    def last_failures(
        self,
    ) -> tuple[ProviderFailure, ...]:


        return tuple(
            self._last_failures
        )





__all__ = [

    "ProviderError",

    "ProviderRateLimitError",

    "ProviderTemporaryUnavailableError",

    "ProviderAuthenticationError",

    "ProviderInvalidDataError",

    "ProviderTimeoutError",

    "ProviderFailure",

    "ProviderHealth",

    "ProviderMetrics",

    "CircuitState",

    "ProviderManager",

]
