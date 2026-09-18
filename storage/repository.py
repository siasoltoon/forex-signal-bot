from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    @abstractmethod
    def get(self, record_id: str) -> T | None:
        raise NotImplementedError

    @abstractmethod
    def save(self, record: T) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, record_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def list(self) -> tuple[T, ...]:
        raise NotImplementedError


class InMemoryRepository(Repository[T]):
    """Deterministic repository used for tests and local domain execution."""

    def __init__(self, key_getter) -> None:
        self._key_getter = key_getter
        self._items: dict[str, T] = {}

    def get(self, record_id: str) -> T | None:
        return self._items.get(record_id)

    def save(self, record: T) -> None:
        key = self._key_getter(record)
        if not key:
            raise ValueError("repository record id is required")
        self._items[key] = record

    def delete(self, record_id: str) -> None:
        self._items.pop(record_id, None)

    def list(self) -> tuple[T, ...]:
        return tuple(self._items.values())
