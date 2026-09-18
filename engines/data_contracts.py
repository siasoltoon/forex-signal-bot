from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Sequence


class DataStatus(str, Enum):
    VALID = "VALID"
    STALE = "STALE"
    INCOMPLETE = "INCOMPLETE"
    INVALID = "INVALID"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class DataQuality:
    score: float
    status: DataStatus
    missing_points: int = 0
    duplicate_points: int = 0
    stale: bool = False
    anomalies: int = 0
    provider: str | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 100.0:
            raise ValueError("data quality score must be between 0 and 100")
        if min(self.missing_points, self.duplicate_points, self.anomalies) < 0:
            raise ValueError("quality counters cannot be negative")


@dataclass(frozen=True)
class MarketDataRequest:
    market: str
    symbol: str
    timeframe: str
    start: datetime | None = None
    end: datetime | None = None
    limit: int | None = None


@dataclass(frozen=True)
class MarketDataResult:
    request: MarketDataRequest
    records: Sequence[Mapping[str, Any]]
    quality: DataQuality
    received_at: datetime
    source: str

    @property
    def usable(self) -> bool:
        return self.quality.status is DataStatus.VALID and self.quality.score > 0


class MarketDataProvider:
    """Interface only: concrete providers belong in infrastructure adapters."""

    name: str

    def fetch(self, request: MarketDataRequest) -> MarketDataResult:
        raise NotImplementedError

    def health(self) -> bool:
        raise NotImplementedError


@dataclass
class ProviderHealth:
    provider: str
    healthy: bool
    latency_ms: float | None = None
    last_success: datetime | None = None
    error: str | None = None


@dataclass
class ProviderPool:
    providers: list[MarketDataProvider] = field(default_factory=list)

    def available(self) -> list[MarketDataProvider]:
        return [provider for provider in self.providers if provider.health()]
