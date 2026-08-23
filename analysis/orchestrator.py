from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Iterable

from analysis.contracts import AnalysisContext, AnalysisOutput, AnalysisRun
from analysis.registry import AnalyzerRegistry


@dataclass(frozen=True)
class AnalysisPolicy:
    """Controls analyzer selection and failure behavior for one run."""

    analyzers: tuple[str, ...] = ()
    fail_fast: bool = False
    minimum_successful: int = 0


class AnalysisOrchestrator:
    """Coordinates analyzers without coupling callers to concrete engines."""

    def __init__(self, registry: AnalyzerRegistry, *, max_workers: int = 1) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be >= 1")
        self.registry = registry
        self.max_workers = max_workers

    def run(
        self,
        context: AnalysisContext,
        analyzers: Iterable[str] | None = None,
        *,
        policy: AnalysisPolicy | None = None,
    ) -> AnalysisRun:
        selected = tuple(analyzers) if analyzers is not None else self.registry.names()
        policy = policy or AnalysisPolicy(analyzers=selected)
        names = policy.analyzers or selected
        if not names:
            return AnalysisRun(context=context, results=())

        if self.max_workers == 1 or len(names) == 1:
            results = tuple(self._execute_one(name, context) for name in names)
        else:
            with ThreadPoolExecutor(max_workers=min(self.max_workers, len(names))) as executor:
                futures = {
                    executor.submit(self._execute_one, name, context): index
                    for index, name in enumerate(names)
                }
                ordered: list[AnalysisOutput | None] = [None] * len(names)
                for future in as_completed(futures):
                    ordered[futures[future]] = future.result()
                results = tuple(item for item in ordered if item is not None)

        run = AnalysisRun(context=context, results=results)
        if policy.fail_fast and run.failed:
            return run
        if policy.minimum_successful and len(run.successful) < policy.minimum_successful:
            return AnalysisRun(
                context=context,
                results=run.results
                + (
                    AnalysisOutput(
                        analyzer="orchestrator",
                        success=False,
                        warnings=("minimum_successful_analyzers_not_reached",),
                        error="Minimum successful analyzer threshold was not reached.",
                    ),
                ),
            )
        return run

    def _execute_one(self, name: str, context: AnalysisContext) -> AnalysisOutput:
        try:
            analyzer = self.registry.create(name)
            result = analyzer.analyze(context)
            if not isinstance(result, AnalysisOutput):
                raise TypeError(f"Analyzer {name!r} returned an invalid result")
            return result
        except Exception as exc:
            return AnalysisOutput(
                analyzer=str(name),
                success=False,
                error=f"{type(exc).__name__}: {exc}",
            )


__all__ = ["AnalysisOrchestrator", "AnalysisPolicy"]
