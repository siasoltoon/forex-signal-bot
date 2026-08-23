from datetime import datetime, timezone

from application.decision_trace import DecisionTrace
from application.persistence.contracts import AnalysisRecord, UserSettings
from application.persistence.memory import InMemoryAnalysisRepository, InMemorySettingsRepository
from application.presets import AnalysisPreset, PresetStore
from application.session import AnalysisSession


def test_analysis_session_deduplicates_selection() -> None:
    session = AnalysisSession("u1")
    session.set_market("forex", "EURUSD")
    session.set_timeframes("1H", "1H", "15m")
    session.set_styles("price_action", "price_action", "smc")
    assert session.timeframes == ("1H", "15m")
    assert session.styles == ("price_action", "smc")


def test_repositories_round_trip() -> None:
    analyses = InMemoryAnalysisRepository()
    settings = InMemorySettingsRepository()
    record = AnalysisRecord("a1", "u1", "forex", "EURUSD", "1H", "WAIT", datetime.now(timezone.utc))
    analyses.save(record)
    settings.save(UserSettings("u1", language="en"))
    assert analyses.get("a1") == record
    assert settings.get("u1").language == "en"


def test_presets_are_user_scoped() -> None:
    store = PresetStore()
    store.save("u1", AnalysisPreset("default", ("smc",)))
    assert store.get("u1", "default") is not None
    assert store.get("u2", "default") is None


def test_decision_trace_preserves_order() -> None:
    trace = DecisionTrace()
    trace.record("data", "validated")
    trace.record("analysis", "completed")
    trace.record("decision", "WAIT")
    assert [item.stage for item in trace.events()] == ["data", "analysis", "decision"]
