from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol


@dataclass(frozen=True, slots=True)
class ReplayBar:
    timestamp: int
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True, slots=True)
class BacktestConfig:
    initial_equity: float = 10_000.0
    fee_rate: float = 0.0
    slippage: float = 0.0


@dataclass(frozen=True, slots=True)
class BacktestTrade:
    timestamp: int
    direction: str
    entry: float
    exit: float
    quantity: float
    pnl: float
    fees: float


@dataclass(frozen=True, slots=True)
class BacktestResult:
    initial_equity: float
    final_equity: float
    trades: tuple[BacktestTrade, ...]


class ReplayStrategy(Protocol):
    def decide(self, bar: ReplayBar) -> str: ...


class BacktestEngine:
    """Causal replay engine: decisions only receive the current replay bar."""

    def run(self, bars: Iterable[ReplayBar], strategy: ReplayStrategy, config: BacktestConfig) -> BacktestResult:
        equity = config.initial_equity
        trades: list[BacktestTrade] = []
        for bar in bars:
            decision = strategy.decide(bar).upper()
            if decision not in {"BUY", "SELL"}:
                continue
            direction = 1.0 if decision == "BUY" else -1.0
            entry = bar.close + direction * config.slippage
            quantity = 1.0
            exit_price = bar.close
            gross = (exit_price - entry) * direction * quantity
            fees = abs(entry * quantity) * config.fee_rate
            pnl = gross - fees
            equity += pnl
            trades.append(BacktestTrade(bar.timestamp, decision, entry, exit_price, quantity, pnl, fees))
        return BacktestResult(config.initial_equity, equity, tuple(trades))
