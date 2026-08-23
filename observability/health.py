from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Callable


class HealthState(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"


@dataclass(frozen=True, slots=True)
class HealthResult:
    component: str
    state: HealthState
    message: str = ""


class HealthRegistry:
    def __init__(self) -> None:
        self._checks: dict[str, Callable[[], HealthResult]] = {}

    def register(self, name: str, check: Callable[[], HealthResult]) -> None:
        if not name.strip():
            raise ValueError("health check name is required")
        self._checks[name] = check

    def run(self) -> tuple[HealthResult, ...]:
        results: list[HealthResult] = []
        for name, check in self._checks.items():
            try:
                result = check()
            except Exception as exc:  # noqa: BLE001
                result = HealthResult(name, HealthState.UNHEALTHY, str(exc))
            results.append(result)
        return tuple(results)
