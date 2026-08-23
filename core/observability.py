from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class LogLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class Event:
    level: LogLevel
    module: str
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    job_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HealthStatus:
    component: str
    healthy: bool
    latency_ms: float | None = None
    message: str = ""


__all__ = ["Event", "HealthStatus", "LogLevel"]
