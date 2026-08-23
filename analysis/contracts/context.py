from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class AnalysisContext:
    """Immutable input context shared by analyzers."""

    symbol: str
    timeframe: str
    market: str = "unknown"
    data: Any = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("symbol cannot be empty")
        if not self.timeframe:
            raise ValueError("timeframe cannot be empty")
