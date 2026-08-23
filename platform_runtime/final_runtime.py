from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from .analysis_runtime import MultiTimeframeEvidence
from .intelligence import AdvancedFusion, IntelligenceDecision
from .risk_portfolio import PositionPlan, RiskEngine, RiskLimits


@dataclass(frozen=True)
class RuntimeRequest:
    market: str
    symbol: str
    timeframes: tuple[str, ...]
    analyzer_names: tuple[str, ...] = ()
    account_size: float | None = None
    risk_percent: float = 1.0
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DecisionTrace:
    trace_id: str
    created_at: datetime
    stages: tuple[str, ...]
    decision: str
    confidence: float
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class RuntimeResult:
    decision: IntelligenceDecision
    position: PositionPlan | None
    trace: DecisionTrace


class FinalRuntime:
    """Deterministic orchestration boundary; external data/models remain injected."""

    def __init__(self, fusion: AdvancedFusion | None = None, risk: RiskEngine | None = None) -> None:
        self.fusion = fusion or AdvancedFusion()
        self.risk = risk or RiskEngine(RiskLimits())

    def decide(self, request: RuntimeRequest, evidence: MultiTimeframeEvidence, data_quality: float, trace_id: str) -> RuntimeResult:
        decision = self.fusion.fuse(evidence, data_quality=data_quality)
        position = None
        entry = request.metadata.get("entry")
        stop = request.metadata.get("stop")
        if decision.decision in {"BUY", "SELL"} and request.account_size is not None and entry is not None and stop is not None:
            position = self.risk.position_size(
                account_size=float(request.account_size),
                entry=float(entry),
                stop=float(stop),
                volatility_factor=float(request.metadata.get("volatility_factor", 1.0)),
            )
        trace = DecisionTrace(
            trace_id=trace_id,
            created_at=datetime.now(timezone.utc),
            stages=("data", "analysis", "fusion", "confidence", "risk", "decision"),
            decision=decision.decision,
            confidence=decision.confidence,
            reasons=decision.reasons,
        )
        return RuntimeResult(decision=decision, position=position, trace=trace)
