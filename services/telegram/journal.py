from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

from .journal_store import JournalStore


@dataclass
class JournalEntry:
    symbol: str
    side: str
    entry: float | None
    stop_loss: float | None
    take_profit: float | None
    notes: str = ""
    status: str = "OPEN"
    result: str | None = None
    created_at: str = ""


_STORE = JournalStore()


def _load(user_id: int) -> list[JournalEntry]:
    return [JournalEntry(**item) for item in _STORE.list(user_id, limit=1000)]


def _save(user_id: int, entries: list[JournalEntry]) -> None:
    _STORE.replace(user_id, [asdict(item) for item in reversed(entries)])


def add_entry(user_id: int, entry: JournalEntry) -> JournalEntry:
    if not entry.created_at:
        entry.created_at = datetime.now(timezone.utc).isoformat()
    entries = _load(user_id)
    entries.append(entry)
    _save(user_id, entries)
    return entry


def list_entries(user_id: int, limit: int = 10) -> list[JournalEntry]:
    entries = _load(user_id)
    return list(reversed(entries))[:limit]


def close_entry(user_id: int, index: int, result: str) -> JournalEntry:
    entries = _load(user_id)
    if index < 0 or index >= len(entries):
        raise IndexError("journal entry not found")
    entry = entries[index]
    entry.status = "CLOSED"
    entry.result = result
    _save(user_id, entries)
    return entry


def format_journal(user_id: int, limit: int = 10) -> str:
    entries = list_entries(user_id, limit)
    if not entries:
        return "📒 <b>ژورنال معاملات</b>\n\nهنوز معامله‌ای ثبت نشده است."
    lines = ["📒 <b>ژورنال معاملات</b>", ""]
    for number, entry in enumerate(entries, 1):
        result = entry.result or entry.status
        lines.append(
            f"{number}. <b>{entry.symbol}</b> {entry.side} | "
            f"ورود {entry.entry if entry.entry is not None else '—'} | "
            f"SL {entry.stop_loss if entry.stop_loss is not None else '—'} | "
            f"TP {entry.take_profit if entry.take_profit is not None else '—'} | {result}"
        )
    return "\n".join(lines)


def export_entries(user_id: int) -> list[dict[str, Any]]:
    return [asdict(entry) for entry in _load(user_id)]


__all__ = ["JournalEntry", "add_entry", "list_entries", "close_entry", "format_journal", "export_entries"]
