from __future__ import annotations

from abc import ABC, abstractmethod

from data.contracts import MarketDataRequest, MarketDataResult


class DataProvider(ABC):
    name: str

    @abstractmethod
    def fetch(self, request: MarketDataRequest) -> MarketDataResult:
        """Return validated provider output or raise a provider-specific error."""
        raise NotImplementedError

    def healthcheck(self) -> bool:
        return True
