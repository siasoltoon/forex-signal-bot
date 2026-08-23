from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, StrEnum


class AlertSeverity(IntEnum):
    NORMAL = 10
    IMPORTANT = 50
    CRITICAL = 100


class NotificationChannel(StrEnum):
    TELEGRAM = "TELEGRAM"
    INTERNAL = "INTERNAL"


@dataclass(frozen=True, slots=True)
class Notification:
    notification_id: str
    user_id: str
    channel: NotificationChannel
    severity: AlertSeverity
    message_key: str
    dedupe_key: str
