from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvaluationRecord:
    strategy_id: str
    window_id: str
    score: float
    drawdown: float
    trades: int


@dataclass(frozen=True, slots=True)
class EvaluationSummary:
    strategy_id: str
    windows: int
    average_score: float
    worst_drawdown: float
    total_trades: int


def summarize(records: tuple[EvaluationRecord, ...]) -> tuple[EvaluationSummary, ...]:
    grouped: dict[str, list[EvaluationRecord]] = {}
    for record in records:
        grouped.setdefault(record.strategy_id, []).append(record)
    result: list[EvaluationSummary] = []
    for strategy_id, items in grouped.items():
        result.append(
            EvaluationSummary(
                strategy_id=strategy_id,
                windows=len(items),
                average_score=sum(item.score for item in items) / len(items),
                worst_drawdown=max(item.drawdown for item in items),
                total_trades=sum(item.trades for item in items),
            )
        )
    return tuple(sorted(result, key=lambda item: item.average_score, reverse=True))
