from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ComponentState(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class Metric:
    name: str
    value: float
    unit: str
    labels: dict[str, str] | None = None


@dataclass(frozen=True, slots=True)
class ComponentHealth:
    component: str
    state: ComponentState
    message: str = ""
    latency_ms: float | None = None


@dataclass(frozen=True, slots=True)
class SystemSnapshot:
    health: tuple[ComponentHealth, ...]
    metrics: tuple[Metric, ...] = ()


__all__ = ["ComponentHealth", "ComponentState", "Metric", "SystemSnapshot"]
