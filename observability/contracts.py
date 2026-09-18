from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class LogEvent:
    timestamp: float
    level: LogLevel
    module: str
    message: str
    job_id: str | None = None
    user_id: str | None = None
    error: str | None = None
    fields: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MetricSample:
    name: str
    value: float
    timestamp: float
    labels: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TraceContext:
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    sampled: bool = True
