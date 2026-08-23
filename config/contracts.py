from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    environment: str
    log_level: str = "INFO"
    max_workers: int = 1
    request_timeout_seconds: float = 30.0
    analysis_timeout_seconds: float = 120.0
    default_language: str = "fa"


@dataclass(frozen=True, slots=True)
class FeatureFlags:
    scanner: bool = False
    live_monitoring: bool = False
    ai_engine: bool = False
    paper_trading: bool = False


__all__ = ["FeatureFlags", "RuntimeConfig"]
