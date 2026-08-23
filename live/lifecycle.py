from __future__ import annotations
from dataclasses import dataclass
from .live_monitor import LiveSignal,TradeState
@dataclass(frozen=True,slots=True)
class LifecycleEvent:
    signal_id:str; previous:TradeState; current:TradeState; reason:str
class TradeLifecycle:
    def transition(self,previous:LiveSignal,current:LiveSignal)->LifecycleEvent|None:
        if previous.state==current.state:return None
        return LifecycleEvent(current.signal_id,previous.state,current.state,f"{previous.state.value}->{current.state.value}")
