from backtest.engine import BacktestConfig, BacktestEngine, ReplayBar
from backtest.evaluation import evaluate
from journal.models import Journal, JournalEntry
from monitoring.signal_lifecycle import LifecycleState, SignalLifecycle, SignalSnapshot


class BuyStrategy:
    def decide(self, bar: ReplayBar) -> str:
        return "BUY"


def test_replay_is_causal_and_evaluated() -> None:
    bars = (ReplayBar(1, 100, 101, 99, 101), ReplayBar(2, 101, 102, 100, 102))
    result = BacktestEngine().run(bars, BuyStrategy(), BacktestConfig(initial_equity=1000))
    metrics = evaluate(result)
    assert metrics.trade_count == 2
    assert result.final_equity == 1002


def test_journal_records_entries() -> None:
    journal = Journal()
    journal.record(JournalEntry("t1", "EURUSD", "BUY", 1.1, 1.2, 0.01, "setup", "trend", "reason"))
    assert journal.get("t1") is not None


def test_signal_lifecycle_marks_invalidation_critical() -> None:
    previous = SignalSnapshot("s1", "BUY", 0.8)
    update = SignalLifecycle().update(previous, confidence=0.3, invalidated=True)
    assert update.current.state == LifecycleState.INVALIDATED
    assert update.severity == "CRITICAL"
