from __future__ import annotations
from typing import Iterable, Iterator, TypeVar

T = TypeVar("T")

class MarketReplay:
    def stream(self, observations: Iterable[T]) -> Iterator[tuple[T, ...]]:
        history: list[T] = []
        for item in observations:
            history.append(item)
            yield tuple(history)
