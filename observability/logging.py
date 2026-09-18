from __future__ import annotations

import json
import time
from typing import Callable

from .contracts import LogEvent, LogLevel


class StructuredLogger:
    def __init__(self, sink: Callable[[str], None] | None = None) -> None:
        self._sink = sink or print

    def log(self, level: LogLevel, module: str, message: str, *, job_id: str | None = None, user_id: str | None = None, error: str | None = None, **fields: object) -> LogEvent:
        event = LogEvent(time.time(), level, module, message, job_id, user_id, error, fields)
        self._sink(json.dumps({"timestamp": event.timestamp, "level": event.level.value, "module": event.module, "message": event.message, "job_id": event.job_id, "user_id": event.user_id, "error": event.error, "fields": dict(event.fields)}, default=str, sort_keys=True))
        return event
