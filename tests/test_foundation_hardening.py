from core.decision import DecisionAction, DecisionEvidence
from core.decision_engine import DecisionEngine
from core.mtf import MultiTimeframeContext, TimeframeView
from core.preferences import AnalysisPreset, UserPreferences
from core.scenario import Scenario, ScenarioType
from jobs.contracts import Job, JobStatus
from workers.contracts import WorkerInfo, WorkerStatus


def test_decision_engine_blocks_high_disagreement() -> None:
    result = DecisionEngine().evaluate(
        [
            DecisionEvidence("a", "BUY", 1.0, 1.0),
            DecisionEvidence("b", "SELL", 1.0, 1.0),
        ],
        data_quality=1.0,
        minimum_confidence=0.1,
        maximum_disagreement=0.2,
    )
    assert result.action is DecisionAction.NO_TRADE
    assert "high_model_disagreement" in result.blockers


def test_decision_engine_accepts_strong_consensus() -> None:
    result = DecisionEngine().evaluate(
        [DecisionEvidence("a", "BUY", 1.0, 1.0), DecisionEvidence("b", "BUY", 0.9, 1.0)],
        data_quality=1.0,
        minimum_confidence=0.1,
    )
    assert result.action is DecisionAction.BUY
    assert result.tradable


def test_foundation_contracts() -> None:
    scenario = Scenario(ScenarioType.BULLISH, 0.7, "breakout", "close below support")
    mtf = MultiTimeframeContext(higher=(TimeframeView("4H", "bullish", 0.8),))
    prefs = UserPreferences(presets=(AnalysisPreset("default", ("technical",)),))
    job = Job("j1", "analysis")
    worker = WorkerInfo("w1", WorkerStatus.IDLE)
    assert scenario.probability == 0.7
    assert len(mtf.views) == 1
    assert prefs.presets[0].name == "default"
    assert job.status is JobStatus.QUEUED
    assert worker.status is WorkerStatus.IDLE
