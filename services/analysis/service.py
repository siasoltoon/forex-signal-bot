from __future__ import annotations

from services.base import BaseService
from core.logger import setup_logger
from analysis.adapters import register_legacy_analyzers
from analysis.registry import AnalyzerRegistry
from analysis.orchestrator import AnalysisOrchestrator
from analysis.contracts import AnalysisContext, AnalysisRun


logger = setup_logger()


class AnalysisService(BaseService):
    """Analysis subsystem lifecycle service."""

    name = "analysis"
    critical = False

    def __init__(self) -> None:
        self.registry = AnalyzerRegistry()
        self.orchestrator = AnalysisOrchestrator(self.registry)
        self.started = False

    async def start(self) -> None:
        """Initialize analyzer registrations."""
        register_legacy_analyzers(self.registry)
        self.started = True
        logger.info("Analysis service started.")

    async def stop(self) -> None:
        """Stop analysis service."""
        self.started = False

    def analyze(
        self,
        context: AnalysisContext,
        analyzers: tuple[str, ...] | None = None,
    ) -> AnalysisRun:
        """Execute analysis through the orchestrator pipeline."""
        return self.orchestrator.run(context, analyzers)

    def health(self) -> dict[str, str]:
        return {
            "service": self.name,
            "status": "running" if self.started else "stopped",
            "critical": str(self.critical).lower(),
        }
