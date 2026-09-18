from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BacktestCostModel:
    spread: float = 0.0
    commission_per_unit: float = 0.0
    slippage: float = 0.0

    def execution_price(self, price: float, side: str) -> float:
        direction = 1 if side.upper() == "BUY" else -1
        return price + direction * (self.spread / 2 + self.slippage)

    def commission(self, quantity: float) -> float:
        return abs(quantity) * self.commission_per_unit


@dataclass(frozen=True, slots=True)
class BacktestExecution:
    entry_price: float
    exit_price: float
    gross_pnl: float
    costs: float
    net_pnl: float


class BacktestExecutionModel:
    def __init__(self, costs: BacktestCostModel | None = None) -> None:
        self.costs = costs or BacktestCostModel()

    def execute(self, *, side: str, entry: float, exit: float, quantity: float) -> BacktestExecution:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        adjusted_entry = self.costs.execution_price(entry, side)
        adjusted_exit = self.costs.execution_price(exit, "SELL" if side.upper() == "BUY" else "BUY")
        sign = 1 if side.upper() == "BUY" else -1
        gross = (adjusted_exit - adjusted_entry) * quantity * sign
        costs = self.costs.commission(quantity)
        return BacktestExecution(adjusted_entry, adjusted_exit, gross, costs, gross - costs)
