from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Protocol


@dataclass(frozen=True, slots=True)
class AnalysisRecord:
    analysis_id: str
    user_id: str
    market: str
    symbol: str
    timeframe: str
    decision: str
    created_at: datetime
    payload: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class UserSettings:
    user_id: str
    language: str = "fa"
    risk_percent: float = 1.0
    report_level: str = "intermediate"
    notifications_enabled: bool = True


class AnalysisRepository(Protocol):
    def save(self, record: AnalysisRecord) -> None: ...
    def get(self, analysis_id: str) -> AnalysisRecord | None: ...
    def list_for_user(self, user_id: str, limit: int = 50) -> tuple[AnalysisRecord, ...]: ...


class SettingsRepository(Protocol):
    def get(self, user_id: str) -> UserSettings | None: ...
    def save(self, settings: UserSettings) -> None: ...
