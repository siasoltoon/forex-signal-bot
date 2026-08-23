from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DecisionTrace:
    """Immutable-at-boundary style audit trail for a single decision."""
    stages: list[dict[str, Any]] = field(default_factory=list)

    def add(self, stage: str, **details: Any) -> None:
        self.stages.append({"stage": stage, "details": details})

    def snapshot(self) -> tuple[dict[str, Any], ...]:
        return tuple(self.stages)
