from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class JournalEntry:
    trade_id: str
    symbol: str
    direction: str
    entry: float
    exit: float | None
    risk: float
    setup: str
    regime: str
    reason: str
    result: str | None = None
    mistakes: tuple[str, ...] = ()


class Journal:
    def __init__(self) -> None:
        self._entries: dict[str, JournalEntry] = {}

    def record(self, entry: JournalEntry) -> None:
        if not entry.trade_id.strip():
            raise ValueError("trade_id is required")
        self._entries[entry.trade_id] = entry

    def get(self, trade_id: str) -> JournalEntry | None:
        return self._entries.get(trade_id)

    def all(self) -> tuple[JournalEntry, ...]:
        return tuple(self._entries.values())
