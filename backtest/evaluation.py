from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from backtest.engine import BacktestResult


@dataclass(frozen=True, slots=True)
class EvaluationMetrics:
    total_return: float
    win_rate: float
    max_drawdown: float
    profit_factor: float | None
    trade_count: int


def evaluate(result: BacktestResult) -> EvaluationMetrics:
    equity = result.initial_equity
    peak = equity
    max_drawdown = 0.0
    wins = 0
    gross_profit = 0.0
    gross_loss = 0.0
    for trade in result.trades:
        equity += trade.pnl
        peak = max(peak, equity)
        drawdown = (peak - equity) / peak if peak else 0.0
        max_drawdown = max(max_drawdown, drawdown)
        if trade.pnl > 0:
            wins += 1
            gross_profit += trade.pnl
        elif trade.pnl < 0:
            gross_loss += abs(trade.pnl)
    count = len(result.trades)
    return EvaluationMetrics(
        total_return=(equity - result.initial_equity) / result.initial_equity if result.initial_equity else 0.0,
        win_rate=wins / count if count else 0.0,
        max_drawdown=max_drawdown,
        profit_factor=(gross_profit / gross_loss) if gross_loss else None,
        trade_count=count,
    )
