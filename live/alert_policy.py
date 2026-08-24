from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum

class AlertPriority(IntEnum):
    NORMAL = 1
    IMPORTANT = 2
    CRITICAL = 3

@dataclass(frozen=True, slots=True)
class Alert:
    key: str
    priority: AlertPriority
    message: str

class AlertDeduplicator:
    def __init__(self) -> None:
        self._seen: set[str] = set()
    def accept(self, alert: Alert) -> bool:
        if alert.key in self._seen:
            return False
        self._seen.add(alert.key)
        return True
