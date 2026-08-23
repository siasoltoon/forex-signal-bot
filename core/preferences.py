from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AnalysisPreset:
    name: str
    styles: tuple[str, ...]
    mode: str = "manual"


@dataclass(frozen=True, slots=True)
class UserPreferences:
    language: str = "fa"
    risk_percent: float = 1.0
    markets: tuple[str, ...] = ()
    symbols: tuple[str, ...] = ()
    timeframes: tuple[str, ...] = ()
    presets: tuple[AnalysisPreset, ...] = ()
    report_level: str = "advanced"
    notifications: bool = True


__all__ = ["AnalysisPreset", "UserPreferences"]
