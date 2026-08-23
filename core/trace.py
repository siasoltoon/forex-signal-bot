from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class DecisionTrace:
    """Immutable audit record for the complete decision path."""

    trace_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    stages: tuple[str, ...] = ()
    values: dict[str, Any] = field(default_factory=dict)

    def add_stage(self, stage: str) -> "DecisionTrace":
        return DecisionTrace(
            trace_id=self.trace_id,
            created_at=self.created_at,
            stages=self.stages + (stage,),
            values=dict(self.values),
        )

    def with_value(self, key: str, value: Any) -> "DecisionTrace":
        values = dict(self.values)
        values[key] = value
        return DecisionTrace(self.trace_id, self.created_at, self.stages, values)


__all__ = ["DecisionTrace"]
