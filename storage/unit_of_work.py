from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass


@dataclass(slots=True)
class UnitOfWork(AbstractContextManager["UnitOfWork"]):
    """Transaction boundary; concrete database adapters can implement commit/rollback."""

    committed: bool = False
    rolled_back: bool = False

    def __enter__(self) -> "UnitOfWork":
        self.committed = False
        self.rolled_back = False
        return self

    def commit(self) -> None:
        if self.rolled_back:
            raise RuntimeError("cannot commit a rolled-back unit of work")
        self.committed = True

    def rollback(self) -> None:
        if self.committed:
            raise RuntimeError("cannot rollback a committed unit of work")
        self.rolled_back = True

    def __exit__(self, exc_type, exc, traceback) -> bool:
        if exc_type is not None:
            self.rollback()
        elif not self.committed:
            self.commit()
        return False
