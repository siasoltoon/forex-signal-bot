from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable

from analysis.contracts import AnalysisContext, AnalysisOutput, AnalysisRun
from analysis.registry import AnalyzerRegistry


class AnalysisOrchestrator:
    """Coordinates analyzers without coupling callers to concrete engines."""

    def __init__(self, registry: AnalyzerRegistry, *, max_workers: int = 1) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be >= 1")
        self.registry = registry
        self.max_workers = max_workers

    def run(self, context: AnalysisContext, analyzers: Iterable[str] | None = None) -> AnalysisRun:
        names = tuple(analyzers) if analyzers is not None else self.registry.names()
        if not names:
            return AnalysisRun(context=context, results=())

        if self.max_workers == 1 or len(names) == 1:
            results = tuple(self._execute_one(name, context) for name in names)
        else:
            with ThreadPoolExecutor(max_workers=min(self.max_workers, len(names))) as executor:
                futures = {executor.submit(self._execute_one, name, context): index for index, name in enumerate(names)}
                ordered: list[AnalysisOutput | None] = [None] * len(names)
                for future in as_completed(futures):
                    ordered[futures[future]] = future.result()
                results = tuple(item for item in ordered if item is not None)

        return AnalysisRun(context=context, results=results)

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
