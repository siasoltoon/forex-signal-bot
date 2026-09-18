from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class EvaluationWindow:
    train_start: int
    train_end: int
    test_start: int
    test_end: int


@dataclass(frozen=True, slots=True)
class EvaluationScore:
    window: EvaluationWindow
    score: float
    trades: int


class WalkForwardPlanner:
    """Builds chronological train/test windows without looking ahead."""

    def __init__(self, train_size: int, test_size: int, step: int | None = None) -> None:
        if train_size <= 0 or test_size <= 0:
            raise ValueError("window sizes must be positive")
        self.train_size = train_size
        self.test_size = test_size
        self.step = step or test_size
        if self.step <= 0:
            raise ValueError("step must be positive")

    def plan(self, timestamps: Sequence[int]) -> tuple[EvaluationWindow, ...]:
        windows: list[EvaluationWindow] = []
        start = 0
        size = len(timestamps)
        while start + self.train_size + self.test_size <= size:
            train_end = start + self.train_size
            test_end = train_end + self.test_size
            windows.append(
                EvaluationWindow(
                    timestamps[start],
                    timestamps[train_end - 1],
                    timestamps[train_end],
                    timestamps[test_end - 1],
                )
            )
            start += self.step
        return tuple(windows)
