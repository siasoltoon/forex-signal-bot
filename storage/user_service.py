from __future__ import annotations

from storage.contracts import UserRecord
from storage.repository import Repository


class UserService:
    def __init__(self, repository: Repository[UserRecord]) -> None:
        self._repository = repository

    def get_or_create(self, user_id: str) -> UserRecord:
        if not user_id:
            raise ValueError("user_id is required")
        existing = self._repository.get(user_id)
        if existing is not None:
            return existing
        record = UserRecord(user_id=user_id)
        self._repository.save(record)
        return record

    def save(self, record: UserRecord) -> None:
        if not record.user_id:
            raise ValueError("user_id is required")
        if not 0 <= record.risk_percent <= 100:
            raise ValueError("risk_percent must be between 0 and 100")
        self._repository.save(record)
