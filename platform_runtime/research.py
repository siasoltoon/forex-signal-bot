from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from .data_runtime import Candle


@dataclass(frozen=True)
class ExecutionCosts:
    spread: float = 0.0
    fee: float = 0.0
    slippage: float = 0.0


@dataclass(frozen=True)
class SimulatedFill:
    price: float
    cost: float


class ExecutionSimulator:
    def __init__(self, costs: ExecutionCosts | None = None) -> None:
        self.costs = costs or ExecutionCosts()

    def fill(self, requested_price: float, side: str, quantity: float) -> SimulatedFill:
        direction = 1 if side.upper() == "BUY" else -1
        price = requested_price + direction * (self.costs.spread / 2 + self.costs.slippage)
        return SimulatedFill(price, abs(price * quantity) * self.costs.fee)


@dataclass(frozen=True)
class BacktestResult:
    trades: int
    pnl: float
    max_drawdown: float
    win_rate: float
    leakage_detected: bool
    overfit_warning: bool


class Backtester:
    def run(self, candles: Sequence[Candle], signal: Callable[[Sequence[Candle]], str], costs: ExecutionCosts | None = None) -> BacktestResult:
        simulator = ExecutionSimulator(costs)
        equity = 0.0
        peak = 0.0
        drawdown = 0.0
        wins = 0
        trades = 0
        for index in range(1, len(candles)):
            history = candles[:index]
            decision = signal(history)
            if decision not in {"BUY", "SELL"}:
                continue
            fill = simulator.fill(candles[index].open, decision, 1.0)
            next_close = candles[index].close
            pnl = (next_close - fill.price) if decision == "BUY" else (fill.price - next_close)
            pnl -= fill.cost
            equity += pnl
            peak = max(peak, equity)
            drawdown = max(drawdown, peak - equity)
            wins += pnl > 0
            trades += 1
        win_rate = wins / trades * 100.0 if trades else 0.0
        return BacktestResult(trades, equity, drawdown, win_rate, False, False)


class HistoricalReplay:
    def __init__(self, candles: Sequence[Candle]) -> None:
        self.candles = tuple(candles)

    def frames(self) -> Iterable[tuple[Candle, ...]]:
        for index in range(1, len(self.candles) + 1):
            yield self.candles[:index]


@dataclass(frozen=True)
class WalkForwardWindow:
    train: tuple[Candle, ...]
    test: tuple[Candle, ...]


def walk_forward(candles: Sequence[Candle], train_size: int, test_size: int, step: int | None = None) -> Iterable[WalkForwardWindow]:
    step = step or test_size
    start = 0
    while start + train_size + test_size <= len(candles):
        yield WalkForwardWindow(tuple(candles[start:start + train_size]), tuple(candles[start + train_size:start + train_size + test_size]))
        start += step
