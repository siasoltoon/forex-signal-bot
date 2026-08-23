from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AlertSeverity(str, Enum):
    NORMAL = "NORMAL"
    IMPORTANT = "IMPORTANT"
    CRITICAL = "CRITICAL"


class AlertType(str, Enum):
    OPPORTUNITY = "OPPORTUNITY"
    RISK = "RISK"
    PRICE = "PRICE"
    BREAKOUT = "BREAKOUT"
    NEWS = "NEWS"
    REGIME_CHANGE = "REGIME_CHANGE"
    MODEL_CHANGE = "MODEL_CHANGE"
    SIGNAL_UPDATE = "SIGNAL_UPDATE"


@dataclass(frozen=True, slots=True)
class Alert:
    alert_id: str
    user_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    dedupe_key: str
    created_at: str


__all__ = ["Alert", "AlertSeverity", "AlertType"]
