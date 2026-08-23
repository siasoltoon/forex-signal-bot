"""Production E2E orchestration gates.

This module intentionally performs no synthetic market/news/macro/ML generation.
External integrations are required to provide real data when enabled.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping


@dataclass(frozen=True)
class ProductionE2EResult:
    stage: str
    passed: bool
    reason: str


REQUIRED_STAGES = (
    "market_data",
    "analyzer_e2e",
    "backtest_strategy",
    "live_intelligence",
    "worker_queue",
    "ai_ml",
    "news_macro",
    "telegram_database",
    "failure_recovery",
    "load_stress",
)


def validate_real_integration(stage: str, context: Mapping[str, Any]) -> ProductionE2EResult:
    """Fail closed unless the integration explicitly reports readiness."""
    if stage not in REQUIRED_STAGES:
        return ProductionE2EResult(stage, False, "unknown production stage")
    if not bool(context.get("real_data")):
        return ProductionE2EResult(stage, False, "real integration data is required")
    if bool(context.get("synthetic_data")):
        return ProductionE2EResult(stage, False, "synthetic data is forbidden")
    if not bool(context.get("healthy")):
        return ProductionE2EResult(stage, False, "integration is not healthy")
    return ProductionE2EResult(stage, True, "ready")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
