from datetime import datetime, timezone

from storage.contracts import AnalysisRecord, JobRecord, TradeRecord, UserRecord
from storage.history_service import AnalysisHistory, TradeJournal
from storage.job_store import JobStore
from storage.repository import InMemoryRepository
from storage.unit_of_work import UnitOfWork
from storage.user_service import UserService


def test_user_service_creates_and_reuses_user() -> None:
    repo = InMemoryRepository(lambda item: item.user_id)
    service = UserService(repo)
    first = service.get_or_create("u1")
    second = service.get_or_create("u1")
    assert first == second


def test_analysis_history_is_scoped_to_user() -> None:
    repo = InMemoryRepository(lambda item: item.analysis_id)
    history = AnalysisHistory(repo)
    now = datetime.now(timezone.utc)
    history.save(AnalysisRecord("a1", "u1", "FOREX", "EURUSD", "1H", "WAIT", None, now))
    history.save(AnalysisRecord("a2", "u2", "FOREX", "GBPUSD", "1H", "WAIT", None, now))
    assert [item.analysis_id for item in history.list_for_user("u1")] == ["a1"]


def test_trade_journal_rejects_invalid_quantity() -> None:
    journal = TradeJournal(InMemoryRepository(lambda item: item.trade_id))
    now = datetime.now(timezone.utc)
    try:
        journal.save(TradeRecord("t1", "u1", None, "EURUSD", "BUY", 1.0, None, 0.0, None, now))
    except ValueError:
        pass
    else:
        raise AssertionError("invalid quantity was accepted")


def test_job_store_queries() -> None:
    store = JobStore(InMemoryRepository(lambda item: item.job_id))
    now = datetime.now(timezone.utc)
    store.put(JobRecord("j1", "ANALYSIS", "HIGH", "QUEUED", now, "w1"))
    assert store.get("j1") is not None
    assert store.by_status("QUEUED")[0].job_id == "j1"
    assert store.by_worker("w1")[0].job_id == "j1"


def test_unit_of_work_commits_and_rolls_back() -> None:
    with UnitOfWork() as unit:
        assert unit.committed is False
    assert unit.committed is True

    try:
        with UnitOfWork() as unit:
            raise RuntimeError("boom")
    except RuntimeError:
        assert unit.rolled_back is True
