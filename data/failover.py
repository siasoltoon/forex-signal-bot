from __future__ import annotations

from dataclasses import dataclass

from data.contracts import MarketDataRequest, MarketDataResult
from data.provider import DataProvider


@dataclass(frozen=True, slots=True)
class ProviderStatus:
    name: str
    healthy: bool
    failures: int = 0


class ProviderUnavailable(RuntimeError):
    pass


class ProviderRouter:
    def __init__(self, providers: tuple[DataProvider, ...], *, max_failures: int = 3) -> None:
        if not providers:
            raise ValueError("at least one provider is required")
        self.providers = providers
        self.max_failures = max_failures
        self._failures: dict[str, int] = {p.name: 0 for p in providers}

    def fetch(self, request: MarketDataRequest) -> MarketDataResult:
        errors: list[str] = []
        for provider in self.providers:
            if self._failures[provider.name] >= self.max_failures:
                continue
            try:
                result = provider.fetch(request)
                if not result.quality.valid:
                    raise ProviderUnavailable(f"{provider.name}: invalid quality")
                self._failures[provider.name] = 0
                return result
            except Exception as exc:
                self._failures[provider.name] += 1
                errors.append(f"{provider.name}: {exc}")
        raise ProviderUnavailable("; ".join(errors) or "no healthy provider")

    def statuses(self) -> tuple[ProviderStatus, ...]:
        return tuple(ProviderStatus(p.name, self._failures[p.name] < self.max_failures, self._failures[p.name]) for p in self.providers)
