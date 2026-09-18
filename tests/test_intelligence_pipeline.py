from __future__ import annotations

from datetime import datetime, timedelta, timezone

from analysis.contracts import AnalysisContext, AnalysisOutput, AnalysisRun
from data.intelligence_gate import MarketDataIntelligenceGate
from application.intelligence_pipeline import IntelligencePipeline


class FakeAnalysis:
    def __init__(self, results):
        self.results = results

    def run(self, context, analyzers=None):
        return AnalysisRun(context=context, results=tuple(self.results))


class FakeStrategy:
    def run(self, analysis):
        return {"count": len(analysis.successful)}


class FakeDecision:
    def evaluate(self, analysis, strategies):
        return {"action": "BUY", "strategies": strategies}


class FakeRisk:
    def __init__(self, allowed=True):
        self.allowed = allowed
        self.blockers = () if allowed else ("risk_limit",)

    def evaluate(self, decision):
        return self


def test_pipeline_rejects_all_failed_analysis() -> None:
    context = AnalysisContext("EURUSD", "1H", [])
    result = IntelligencePipeline(FakeAnalysis([AnalysisOutput("x", False, error="boom")])).run(context=context)
    assert result.blocked
    assert result.blockers == ("no_successful_analysis",)
    assert result.trace[-1] == "no_trade"


def test_pipeline_runs_analysis_strategy_decision_and_risk() -> None:
    output = AnalysisOutput("technical", True, values={"direction": "BUY"}, confidence=0.8)
    context = AnalysisContext("EURUSD", "1H", object())
    result = IntelligencePipeline(
        FakeAnalysis([output]),
        strategy=FakeStrategy(),
        decision=FakeDecision(),
        risk=FakeRisk(),
    ).run(context=context)
    assert not result.blocked
    assert result.decision["action"] == "BUY"
    assert result.trace == ("request", "validated_data", "analysis", "strategy", "decision", "risk")


def test_data_gate_rejects_duplicate_or_stale_data() -> None:
    from data.models import Candle

    now = datetime.now(timezone.utc)
    old = now - timedelta(hours=10)
    candle = Candle("EURUSD", old, 1, 1, 1, 1, 1)
    gate = MarketDataIntelligenceGate(timeframe=timedelta(hours=1))
    result = gate.inspect(symbol="EURUSD", timeframe="1H", data=[candle, candle], now=now)
    assert not result.accepted
    assert "data_quality" in result.blockers or "stale_data" in result.blockers
