from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence


class BacktestMode(str, Enum):
    STANDARD = "STANDARD"
    WALK_FORWARD = "WALK_FORWARD"
    OUT_OF_SAMPLE = "OUT_OF_SAMPLE"
    STRESS = "STRESS"


@dataclass(frozen=True)
class ExecutionCostModel:
    fee_bps: float = 0.0
    spread_bps: float = 0.0
    slippage_bps: float = 0.0

    def total_bps(self) -> float:
        return self.fee_bps + self.spread_bps + self.slippage_bps


@dataclass(frozen=True)
class BacktestRequest:
    strategy_id: str
    market: str
    symbol: str
    timeframe: str
    start: str
    end: str
    mode: BacktestMode = BacktestMode.STANDARD
    costs: ExecutionCostModel = field(default_factory=ExecutionCostModel)


@dataclass(frozen=True)
class BacktestResult:
    request: BacktestRequest
    trades: int
    net_return: float
    max_drawdown: float
    win_rate: float
    leakage_detected: bool = False
    overfit_warning: bool = False
    notes: Sequence[str] = ()

    @property
    def valid(self) -> bool:
        return not self.leakage_detected


class BacktestEngine:
    """Contract boundary. Real historical data/execution simulation is an adapter concern."""

    def run(self, request: BacktestRequest, records: Sequence[object]) -> BacktestResult:
        raise NotImplementedError
