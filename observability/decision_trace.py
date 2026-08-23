from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class TraceStep:
    name: str
    status: str
    details: Mapping[str, object]


class DecisionTrace:
    def __init__(self, trace_id: str) -> None:
        if not trace_id.strip():
            raise ValueError("trace_id is required")
        self.trace_id = trace_id
        self._steps: list[TraceStep] = []

    def add(self, name: str, status: str, **details: object) -> None:
        self._steps.append(TraceStep(name, status, details))

    def steps(self) -> tuple[TraceStep, ...]:
        return tuple(self._steps)

    def as_dict(self) -> dict[str, object]:
        return {"trace_id": self.trace_id, "steps": [{"name": s.name, "status": s.status, "details": dict(s.details)} for s in self._steps]}
