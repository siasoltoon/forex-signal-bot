from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
from market_runtime.contracts import Candle
@dataclass(frozen=True, slots=True)
class ReplayFrame:
    index: int
    candles: tuple[Candle,...]
class MarketReplay:
    def replay(self,candles:Sequence[Candle],warmup:int=1):
        for i in range(max(0,warmup),len(candles)):
            yield ReplayFrame(i,tuple(candles[:i+1]))
@dataclass(frozen=True, slots=True)
class Split:
    train: tuple[Candle,...]
    validation: tuple[Candle,...]
    test: tuple[Candle,...]
class ResearchSplitter:
    def split(self,candles:Sequence[Candle],train_ratio=.6,validation_ratio=.2)->Split:
        n=len(candles); a=int(n*train_ratio); b=a+int(n*validation_ratio)
        return Split(tuple(candles[:a]),tuple(candles[a:b]),tuple(candles[b:]))
class WalkForward:
    def windows(self,candles:Sequence[Candle],train_size:int,test_size:int,step:int|None=None):
        step=step or test_size; i=train_size
        while i+test_size<=len(candles):
            yield tuple(candles[i-train_size:i]),tuple(candles[i:i+test_size]); i+=step
