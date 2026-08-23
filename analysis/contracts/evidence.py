from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class AnalysisEvidence:
    """Traceable evidence supporting an analyzer result."""

    source: str
    description: str
    value: Any = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source:
            raise ValueError("evidence source cannot be empty")
        if not self.description:
            raise ValueError("evidence description cannot be empty")
