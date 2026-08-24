from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from services.telegram.journal_store import JournalStore
from services.telegram.tracker import TrackedSignal, track_report, list_tracking, stop_tracking


class Report:
    signal = "BUY"
    entry_price = 100.0
    stop_loss = 95.0
    take_profit_1 = 105.0
    take_profit_2 = 110.0
    take_profit_3 = 115.0


def test_tracker_lifecycle():
    item = track_report(7, "EURUSD", "M15", Report())
    assert item.status == "ACTIVE"
    assert len(list_tracking(7)) == 1
    assert stop_tracking(7, "EURUSD", "M15") is True
    assert list_tracking(7) == []


def test_journal_persists_between_instances():
    with tempfile.TemporaryDirectory() as directory:
        path = str(Path(directory) / "journal.json")
        first = JournalStore(path)
        first.add(7, {"symbol": "EURUSD", "side": "BUY"})
        second = JournalStore(path)
        assert second.list(7) == [{"symbol": "EURUSD", "side": "BUY"}]
