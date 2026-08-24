from live.live_monitor import LiveMonitor,LiveSignal,TradeState
from live.alerts import Alert,AlertEngine
from live.lifecycle import TradeLifecycle

def signal(): return LiveSignal('s1','BUY',100,95,110,.9,TradeState.ACTIVE)
def test_signal_weakening(): assert LiveMonitor().evaluate(signal(),102,.5).state==TradeState.WEAKENING
def test_signal_tp(): assert LiveMonitor().evaluate(signal(),110,.9).state==TradeState.TP
def test_alert_dedup():
    e=AlertEngine(); a=Alert('x','changed'); assert e.emit(a)==a and e.emit(a) is None
def test_lifecycle():
    old=signal(); new=LiveMonitor().evaluate(old,110,.9); assert TradeLifecycle().transition(old,new) is not None
