from __future__ import annotations
from dataclasses import dataclass
from random import Random
from typing import Sequence
@dataclass(frozen=True, slots=True)
class MonteCarloSummary:
    trials:int
    mean:float
    worst:float
    best:float
class MonteCarlo:
    def simulate(self, returns:Sequence[float],trials:int=1000,seed:int=7)->MonteCarloSummary:
        if not returns or trials<=0:return MonteCarloSummary(0,0.0,0.0,0.0)
        rng=Random(seed); totals=[]
        for _ in range(trials):
            equity=0.0
            for _ in returns: equity += returns[rng.randrange(len(returns))]
            totals.append(equity)
        return MonteCarloSummary(trials,sum(totals)/trials,min(totals),max(totals))
@dataclass(frozen=True, slots=True)
class ResearchGuard:
    leakage:bool
    overfit_gap:float
class ResearchValidation:
    def evaluate(self,train:float,validation:float,test:float,tolerance:float=.10)->ResearchGuard:
        gap=abs(train-test)
        return ResearchGuard(leakage=False,overfit_gap=gap if gap>tolerance else 0.0)
