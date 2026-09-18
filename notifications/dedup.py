from __future__ import annotations

from application.idempotency import IdempotencyGuard
from notifications.contracts import Notification


class NotificationDeduplicator:
    def __init__(self, ttl_seconds: float = 300.0) -> None:
        self._guard = IdempotencyGuard(ttl_seconds)

    def should_send(self, notification: Notification) -> bool:
        return self._guard.accept(notification.dedupe_key)
