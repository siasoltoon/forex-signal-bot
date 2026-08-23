"""Final production runtime gate.

This module is intentionally provider/transport agnostic. It coordinates readiness
checks and prevents a degraded dependency from being treated as production-ready.
No synthetic market, news, macro, or ML values are generated here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import monotonic
from typing import Callable, Iterable


class RuntimeStatus(str, Enum):
    READY = "ready"
    DEGRADED = "degraded"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class DependencyCheck:
    name: str
    healthy: bool
    required: bool = True
    detail: str = ""
    latency_ms: float | None = None


@dataclass(frozen=True)
class RuntimeReadiness:
    status: RuntimeStatus
    checks: tuple[DependencyCheck, ...]
    reasons: tuple[str, ...] = ()

    @property
    def ready(self) -> bool:
        return self.status is RuntimeStatus.READY


@dataclass
class FinalRuntimeGate:
    """Central fail-closed readiness gate for live execution."""

    checks: dict[str, Callable[[], DependencyCheck]] = field(default_factory=dict)

    def register(self, name: str, check: Callable[[], DependencyCheck]) -> None:
        if not name.strip():
            raise ValueError("check name must not be empty")
        self.checks[name] = check

    def evaluate(self, required: Iterable[str] | None = None) -> RuntimeReadiness:
        names = tuple(required) if required is not None else tuple(self.checks)
        results: list[DependencyCheck] = []
        reasons: list[str] = []
        for name in names:
            check_fn = self.checks.get(name)
            if check_fn is None:
                result = DependencyCheck(name=name, healthy=False, required=True, detail="missing check")
            else:
                started = monotonic()
                try:
                    result = check_fn()
                except Exception as exc:  # noqa: BLE001 - boundary must fail closed
                    result = DependencyCheck(name=name, healthy=False, required=True, detail=f"check error: {exc}")
                if result.latency_ms is None:
                    result = DependencyCheck(
                        name=result.name,
                        healthy=result.healthy,
                        required=result.required,
                        detail=result.detail,
                        latency_ms=round((monotonic() - started) * 1000, 2),
                    )
            results.append(result)
            if not result.healthy:
                reasons.append(f"{result.name}: {result.detail or 'unhealthy'}")

        required_failures = [r for r in results if r.required and not r.healthy]
        optional_failures = [r for r in results if not r.required and not r.healthy]
        if required_failures:
            status = RuntimeStatus.BLOCKED
        elif optional_failures:
            status = RuntimeStatus.DEGRADED
        else:
            status = RuntimeStatus.READY
        return RuntimeReadiness(status=status, checks=tuple(results), reasons=tuple(reasons))

    def require_ready(self, required: Iterable[str] | None = None) -> RuntimeReadiness:
        readiness = self.evaluate(required)
        if not readiness.ready:
            raise RuntimeError("production runtime is not ready: " + "; ".join(readiness.reasons))
        return readiness
