from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from .context import AnalysisContext
from .result import AnalysisResult


class Analyzer(ABC):
    """Contract implemented by every analysis plugin."""

    analyzer_id: ClassVar[str]
    version: ClassVar[str] = "1.0"

    @abstractmethod
    def supports(self, context: AnalysisContext) -> bool:
        """Return whether this analyzer can process the supplied context."""
        raise NotImplementedError

    @abstractmethod
    def analyze(self, context: AnalysisContext) -> AnalysisResult:
        """Analyze the supplied context and return a normalized result."""
        raise NotImplementedError
