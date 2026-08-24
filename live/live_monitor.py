from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
class TradeState(str,Enum): ACTIVE="ACTIVE"; WEAKENING="WEAKENING"; INVALIDATED="INVALIDATED"; TP="TP"; SL="SL"; EXPIRED="EXPIRED"
@dataclass(frozen=True,slots=True)
class LiveSignal:
    signal_id:str; direction:str; entry:float; stop:float; target:float; confidence:float; state:TradeState
class LiveMonitor:
    def evaluate(self,s:LiveSignal,price:float,confidence:float)->LiveSignal:
        state=s.state
        if s.direction=="BUY":
            if price<=s.stop: state=TradeState.SL
            elif price>=s.target: state=TradeState.TP
            elif confidence<s.confidence*0.7: state=TradeState.WEAKENING
        elif s.direction=="SELL":
            if price>=s.stop: state=TradeState.SL
            elif price<=s.target: state=TradeState.TP
            elif confidence<s.confidence*0.7: state=TradeState.WEAKENING
        return LiveSignal(s.signal_id,s.direction,s.entry,s.stop,s.target,confidence,state)
