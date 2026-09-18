from __future__ import annotations

from storage.contracts import AnalysisRecord, SignalRecord, TradeRecord
from storage.repository import Repository


class AnalysisHistory:
    def __init__(self, repository: Repository[AnalysisRecord]) -> None:
        self._repository = repository

    def save(self, record: AnalysisRecord) -> None:
        self._repository.save(record)

    def get(self, analysis_id: str) -> AnalysisRecord | None:
        return self._repository.get(analysis_id)

    def list_for_user(self, user_id: str) -> tuple[AnalysisRecord, ...]:
        return tuple(item for item in self._repository.list() if item.user_id == user_id)


class SignalHistory:
    def __init__(self, repository: Repository[SignalRecord]) -> None:
        self._repository = repository

    def save(self, record: SignalRecord) -> None:
        self._repository.save(record)

    def list_for_user(self, user_id: str) -> tuple[SignalRecord, ...]:
        return tuple(item for item in self._repository.list() if item.user_id == user_id)


class TradeJournal:
    def __init__(self, repository: Repository[TradeRecord]) -> None:
        self._repository = repository

    def save(self, record: TradeRecord) -> None:
        if record.quantity <= 0:
            raise ValueError("quantity must be positive")
        self._repository.save(record)

    def list_for_user(self, user_id: str) -> tuple[TradeRecord, ...]:
        return tuple(item for item in self._repository.list() if item.user_id == user_id)
