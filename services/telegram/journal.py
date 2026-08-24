from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any


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


JOURNALS: dict[int, list[JournalEntry]] = {}


def add_entry(user_id: int, entry: JournalEntry) -> JournalEntry:
    if not entry.created_at:
        entry.created_at = datetime.now(timezone.utc).isoformat()
    JOURNALS.setdefault(user_id, []).append(entry)
    return entry


def list_entries(user_id: int, limit: int = 10) -> list[JournalEntry]:
    return list(reversed(JOURNALS.get(user_id, [])))[:limit]


def close_entry(user_id: int, index: int, result: str) -> JournalEntry:
    entries = JOURNALS.get(user_id, [])
    if index < 0 or index >= len(entries):
        raise IndexError("journal entry not found")
    entry = entries[index]
    entry.status = "CLOSED"
    entry.result = result
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
    return [asdict(entry) for entry in JOURNALS.get(user_id, [])]


__all__ = ["JournalEntry", "add_entry", "list_entries", "close_entry", "format_journal", "export_entries"]
