from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EvaluationMode(str, Enum):
    BACKTEST = "BACKTEST"
    WALK_FORWARD = "WALK_FORWARD"
    OUT_OF_SAMPLE = "OUT_OF_SAMPLE"
    MONTE_CARLO = "MONTE_CARLO"
    STRESS = "STRESS"


@dataclass(frozen=True, slots=True)
class BacktestConfig:
    symbol: str
    timeframe: str
    start: str
    end: str
    fee_rate: float = 0.0
    spread: float = 0.0
    slippage: float = 0.0
    mode: EvaluationMode = EvaluationMode.BACKTEST


@dataclass(frozen=True, slots=True)
class BacktestResult:
    trades: int
    net_return: float
    max_drawdown: float
    win_rate: float
    profit_factor: float | None
    leakage_detected: bool = False
    overfit_warning: bool = False


__all__ = ["BacktestConfig", "BacktestResult", "EvaluationMode"]
