from __future__ import annotations

from dataclasses import dataclass

from engines.confidence import ConfidenceResult
from engines.decision_trace import DecisionTrace
from engines.scenario_engine import Scenario


@dataclass(frozen=True, slots=True)
class DecisionResult:
    decision: str
    score: float
    confidence: float
    reason: str
    trace: tuple[dict, ...]


class DecisionEngine:
    def decide(
        self,
        score: float,
        confidence: ConfidenceResult,
        scenarios: tuple[Scenario, ...],
        risk_blocked: bool = False,
        event_blocked: bool = False,
    ) -> DecisionResult:
        trace = DecisionTrace()
        trace.add("analysis", score=score)
        trace.add("confidence", score=confidence.score, disagreement=confidence.disagreement)
        trace.add("risk", blocked=risk_blocked)
        trace.add("event", blocked=event_blocked)
        if confidence.blocked or risk_blocked or event_blocked:
            decision = "NO_TRADE"
            reason = "Decision blocked by confidence, risk, or event constraints"
        elif score > 0.2:
            decision = "BUY"
            reason = "Weighted evidence supports bullish direction"
        elif score < -0.2:
            decision = "SELL"
            reason = "Weighted evidence supports bearish direction"
        else:
            decision = "WAIT"
            reason = "Evidence is insufficient for directional action"
        trace.add("decision", decision=decision, reason=reason)
        return DecisionResult(decision, score, confidence.score, reason, trace.snapshot())
