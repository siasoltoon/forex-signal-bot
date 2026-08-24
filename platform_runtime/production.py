from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class AuditEvent:
    event: str
    module: str
    severity: Severity
    job_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AuditLog:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def record(self, event: AuditEvent) -> None:
        self.events.append(event)


class ChampionChallenger:
    def __init__(self, champion: str) -> None:
        self.champion = champion
        self.challenger: str | None = None

    def propose(self, challenger: str) -> None:
        self.challenger = challenger

    def promote(self, challenger_score: float, champion_score: float, margin: float = 0.0) -> bool:
        if self.challenger and challenger_score > champion_score + margin:
            self.champion = self.challenger
            self.challenger = None
            return True
        return False


@dataclass(frozen=True)
class HealthStatus:
    component: str
    healthy: bool
    details: dict[str, Any] = field(default_factory=dict)


class HealthRegistry:
    def __init__(self) -> None:
        self._statuses: dict[str, HealthStatus] = {}

    def update(self, status: HealthStatus) -> None:
        self._statuses[status.component] = status

    def all(self) -> tuple[HealthStatus, ...]:
        return tuple(self._statuses.values())

    def healthy(self) -> bool:
        return all(item.healthy for item in self._statuses.values())
