from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: str
    actor_id: str
    action: str
    resource: str
    success: bool
    timestamp: datetime
    metadata: tuple[tuple[str, str], ...] = ()

    @classmethod
    def create(cls, event_id: str, actor_id: str, action: str, resource: str, success: bool, metadata: tuple[tuple[str, str], ...] = ()) -> "AuditEvent":
        return cls(event_id, actor_id, action, resource, success, datetime.now(timezone.utc), metadata)
