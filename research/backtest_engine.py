from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Sequence

@dataclass(frozen=True, slots=True)
class BacktestTrade:
    entry_index: int
    exit_index: int
    entry: float
    exit: float
    pnl: float

@dataclass(frozen=True, slots=True)
class BacktestResult:
    trades: tuple[BacktestTrade, ...]
    pnl: float
    max_drawdown: float

class BacktestEngine:
    def run(self, prices: Sequence[float], signal: Callable[[Sequence[float]], int], fee_rate: float = 0.0, slippage: float = 0.0) -> BacktestResult:
        if len(prices) < 2:
            return BacktestResult((), 0.0, 0.0)
        trades: list[BacktestTrade] = []
        equity = peak = 0.0
        entry_index: int | None = None
        direction = 0
        for i in range(1, len(prices)):
            decision = signal(prices[:i])
            if entry_index is None and decision in (-1, 1):
                entry_index, direction = i, decision
            elif entry_index is not None and decision == -direction:
                entry = prices[entry_index] * (1 + slippage * direction)
                exit_price = prices[i] * (1 - slippage * direction)
                gross = direction * (exit_price - entry)
                pnl = gross - abs(entry) * fee_rate - abs(exit_price) * fee_rate
                equity += pnl
                peak = max(peak, equity)
                trades.append(BacktestTrade(entry_index, i, entry, exit_price, pnl))
                entry_index = None
                direction = 0
        drawdown = max(0.0, peak - equity)
        return BacktestResult(tuple(trades), equity, drawdown)
