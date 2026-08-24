from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from random import Random
from typing import Protocol, Sequence

from .data_runtime import Candle


@dataclass(frozen=True)
class Order:
    side: str
    quantity: float
    price: float
    stop: float | None = None
    target: float | None = None


@dataclass(frozen=True)
class Fill:
    side: str
    quantity: float
    price: float
    fee: float
    slippage: float


@dataclass(frozen=True)
class BacktestResult:
    equity_curve: tuple[float, ...]
    trades: int
    wins: int
    losses: int
    net_pnl: float
    max_drawdown: float
    win_rate: float
    sharpe: float


class Strategy(Protocol):
    name: str
    def on_candle(self, candles: Sequence[Candle], cash: float) -> Order | None: ...


class ExecutionSimulator:
    def __init__(self, fee_rate: float = 0.0, slippage_bps: float = 0.0) -> None:
        self.fee_rate = fee_rate
        self.slippage_bps = slippage_bps

    def fill(self, order: Order) -> Fill:
        direction = 1 if order.side.upper() == "BUY" else -1
        slip = order.price * self.slippage_bps / 10_000
        price = order.price + direction * slip
        fee = abs(price * order.quantity) * self.fee_rate
        return Fill(order.side.upper(), order.quantity, price, fee, slip)


class HistoricalReplay:
    def __init__(self, candles: Sequence[Candle]) -> None:
        self.candles = tuple(sorted(candles, key=lambda c: c.timestamp))

    def frames(self):
        for index in range(1, len(self.candles) + 1):
            yield self.candles[:index]


def run_backtest(candles: Sequence[Candle], strategy: Strategy, starting_cash: float = 10_000.0, execution: ExecutionSimulator | None = None) -> BacktestResult:
    execution = execution or ExecutionSimulator()
    cash, position, entry = starting_cash, 0.0, None
    equity: list[float] = []
    pnls: list[float] = []
    for frame in HistoricalReplay(candles).frames():
        last = frame[-1]
        order = strategy.on_candle(frame, cash)
        if order:
            fill = execution.fill(order)
            signed = fill.quantity if fill.side == "BUY" else -fill.quantity
            if position == 0:
                position, entry = signed, fill.price
                cash -= signed * fill.price + fill.fee
            elif position * signed < 0:
                close_qty = min(abs(position), abs(signed))
                pnl = (fill.price - float(entry)) * close_qty * (1 if position > 0 else -1) - fill.fee
                pnls.append(pnl)
                cash += close_qty * fill.price - fill.fee
                position = 0.0
                entry = None
        equity.append(cash + position * last.close)
    if position and entry is not None:
        pnl = (equity[-1] - cash) - abs(position) * float(entry)
        pnls.append(pnl)
    peak = starting_cash
    max_dd = 0.0
    returns = []
    previous = starting_cash
    for value in equity:
        peak = max(peak, value)
        max_dd = max(max_dd, (peak - value) / peak if peak else 0.0)
        returns.append((value - previous) / previous if previous else 0.0)
        previous = value
    mean = sum(returns) / len(returns) if returns else 0.0
    variance = sum((r - mean) ** 2 for r in returns) / max(1, len(returns) - 1)
    sharpe = mean / sqrt(variance) * sqrt(252) if variance > 0 else 0.0
    wins = sum(p > 0 for p in pnls)
    losses = sum(p <= 0 for p in pnls)
    return BacktestResult(tuple(equity), len(pnls), wins, losses, sum(pnls), max_dd, wins / len(pnls) if pnls else 0.0, sharpe)


def walk_forward(candles: Sequence[Candle], strategy_factory, train_size: int, test_size: int):
    if train_size <= 0 or test_size <= 0:
        raise ValueError("train_size and test_size must be positive")
    results = []
    start = 0
    while start + train_size + test_size <= len(candles):
        train = tuple(candles[start:start + train_size])
        test = tuple(candles[start + train_size:start + train_size + test_size])
        strategy = strategy_factory(train)
        results.append(run_backtest(test, strategy))
        start += test_size
    return tuple(results)


def monte_carlo(trade_pnls: Sequence[float], simulations: int = 1000, seed: int = 7) -> tuple[float, ...]:
    if not trade_pnls:
        return ()
    rng = Random(seed)
    terminal = []
    for _ in range(simulations):
        sample = [trade_pnls[rng.randrange(len(trade_pnls))] for _ in trade_pnls]
        terminal.append(sum(sample))
    return tuple(terminal)
