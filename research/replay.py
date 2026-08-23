from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, Sequence, TypeVar

from market_runtime.contracts import Candle

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ReplayFrame:
    index: int
    candles: tuple[Candle, ...]


class MarketReplay:
    def stream(self, observations: Iterable[T]) -> Iterator[tuple[T, ...]]:
        """Yield causal history snapshots without exposing future observations."""
        history: list[T] = []
        for item in observations:
            history.append(item)
            yield tuple(history)

    def replay(
        self, candles: Sequence[Candle], warmup: int = 1
    ) -> Iterator[ReplayFrame]:
        """Replay candles causally; each frame contains only data available at its index."""
        for i in range(max(0, warmup), len(candles)):
            yield ReplayFrame(i, tuple(candles[: i + 1]))


@dataclass(frozen=True, slots=True)
class Split:
    train: tuple[Candle, ...]
    validation: tuple[Candle, ...]
    test: tuple[Candle, ...]


class ResearchSplitter:
    def split(
        self,
        candles: Sequence[Candle],
        train_ratio: float = 0.6,
        validation_ratio: float = 0.2,
    ) -> Split:
        if not 0 < train_ratio < 1:
            raise ValueError("train_ratio must be between 0 and 1")
        if not 0 <= validation_ratio < 1:
            raise ValueError("validation_ratio must be between 0 and 1")
        if train_ratio + validation_ratio > 1:
            raise ValueError("train_ratio + validation_ratio cannot exceed 1")
        n = len(candles)
        a = int(n * train_ratio)
        b = a + int(n * validation_ratio)
        return Split(tuple(candles[:a]), tuple(candles[a:b]), tuple(candles[b:]))


class WalkForward:
    def windows(
        self,
        candles: Sequence[Candle],
        train_size: int,
        test_size: int,
        step: int | None = None,
    ):
        if train_size <= 0 or test_size <= 0:
            raise ValueError("train_size and test_size must be positive")
        step = step or test_size
        if step <= 0:
            raise ValueError("step must be positive")
        i = train_size
        while i + test_size <= len(candles):
            yield (
                tuple(candles[i - train_size : i]),
                tuple(candles[i : i + test_size]),
            )
            i += step
