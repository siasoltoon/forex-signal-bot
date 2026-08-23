from __future__ import annotations

from dataclasses import dataclass

from .analysis_runtime import AnalysisOrchestrator, AnalyzerRegistry, MultiTimeframeEvidence
from .data_runtime import MarketSnapshot
from .intelligence import AdvancedFusion, IntelligenceDecision
from .production import AuditEvent, AuditLog, Severity
from .risk_portfolio import PositionPlan, RiskEngine, RiskLimits


@dataclass(frozen=True)
class PipelineRequest:
    snapshots: tuple[MarketSnapshot, ...]
    analyzer_names: tuple[str, ...] = ()
    account_size: float = 0.0
    entry: float = 0.0
    stop: float = 0.0
    volatility_factor: float = 1.0
    data_quality: float = 100.0


@dataclass(frozen=True)
class PipelineResult:
    evidence: MultiTimeframeEvidence
    decision: IntelligenceDecision
    position: PositionPlan
    blocked: bool
    reasons: tuple[str, ...]


class IntelligencePipeline:
    """Deterministic boundary from validated snapshots to a risk-aware decision."""

    def __init__(self, analyzers: AnalyzerRegistry, fusion: AdvancedFusion | None = None, risk: RiskEngine | None = None, audit: AuditLog | None = None) -> None:
        self.analysis = AnalysisOrchestrator(analyzers)
        self.fusion = fusion or AdvancedFusion()
        self.risk = risk or RiskEngine(RiskLimits())
        self.audit = audit

    async def run(self, request: PipelineRequest) -> PipelineResult:
        if not request.snapshots:
            raise ValueError("at least one validated market snapshot is required")
        evidence = await self.analysis.run(request.snapshots, request.analyzer_names or None)
        decision = self.fusion.fuse(evidence, data_quality=request.data_quality)
        position = self.risk.position_size(request.account_size, request.entry, request.stop, request.volatility_factor)
        reasons = list(decision.reasons) + list(position.reasons)
        blocked = decision.decision == "NO TRADE" or position.blocked
        if blocked:
            reasons.append("pipeline_blocked")
        if self.audit:
            self.audit.record(AuditEvent(
                event="decision_pipeline",
                module="intelligence_pipeline",
                severity=Severity.INFO if not blocked else Severity.WARNING,
                metadata={"decision": decision.decision, "score": decision.score, "confidence": decision.confidence, "disagreement": decision.disagreement, "blocked": blocked},
            ))
        return PipelineResult(evidence, decision, position, blocked, tuple(dict.fromkeys(reasons)))


__all__ = ["IntelligencePipeline", "PipelineRequest", "PipelineResult"]
