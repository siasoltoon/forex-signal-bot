from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
from market_runtime.contracts import Candle
@dataclass(frozen=True, slots=True)
class Trade:
    side: str
    entry: float
    stop: float
    target: float
    quantity: float = 1.0
@dataclass(frozen=True, slots=True)
class BacktestResult:
    trades: int
    pnl: float
    max_drawdown: float
    win_rate: float
class ExecutionSimulator:
    def __init__(self, fee_rate: float=0.0, slippage: float=0.0) -> None: self.fee_rate=fee_rate; self.slippage=slippage
    def fill(self, trade: Trade) -> float:
        return trade.entry + (self.slippage if trade.side=="BUY" else -self.slippage)
    def pnl(self, trade: Trade, exit_price: float) -> float:
        direction=1 if trade.side=="BUY" else -1
        gross=(exit_price-self.fill(trade))*direction*trade.quantity
        return gross-abs(exit_price*trade.quantity)*self.fee_rate-abs(trade.entry*trade.quantity)*self.fee_rate
class BacktestEngine:
    def run(self, candles: Sequence[Candle], trades: Sequence[Trade]) -> BacktestResult:
        results=[]
        for t in trades:
            exit_price=t.target if (t.side=="BUY" and any(c.high>=t.target for c in candles)) or (t.side=="SELL" and any(c.low<=t.target for c in candles)) else t.stop
            results.append(self._pnl(t,exit_price))
        equity=0.0; peak=0.0; dd=0.0
        for x in results:
            equity+=x; peak=max(peak,equity); dd=max(dd,peak-equity)
        return BacktestResult(len(results),sum(results),dd,(sum(x>0 for x in results)/len(results)) if results else 0.0)
    def _pnl(self,t:Trade,exit_price:float)->float:
        return ExecutionSimulator().pnl(t,exit_price)
