from engines.advanced_fusion import AdvancedFusionEngine, Evidence
from engines.confidence_calibration import ConfidenceCalibrator
from market.data_quality import MarketDataValidator
from market.provider_contracts import Candle
from research.evaluation import ResearchEvaluator
from research.replay import MarketReplay
from live.signal_monitor import SignalMonitor, SignalState
from infrastructure.security import RequestAuthenticator
from macro.event_contracts import EventImpact, EventRiskGate, MarketEvent


def test_advanced_fusion_penalizes_disagreement():
    result = AdvancedFusionEngine().combine([Evidence("a", "BULLISH", 1), Evidence("b", "BEARISH", 1)])
    assert result.disagreement == 1


def test_confidence_calibration():
    assert 0 <= ConfidenceCalibrator().calibrate(.9, .8, .1, .9).calibrated <= 1


def test_data_quality_rejects_bad_ohlc():
    candles = (Candle(1, 10, 9, 8, 9),)
    assert not MarketDataValidator().validate(candles).valid


def test_research_split_is_causal():
    split = ResearchEvaluator().split(tuple(range(10)))
    assert split.train[-1] < split.validation[0] < split.test[0]
    assert not ResearchEvaluator().detect_leakage(split.train, split.test)


def test_replay_never_exposes_future():
    assert list(MarketReplay().stream([1, 2, 3]))[-1] == (1, 2, 3)


def test_live_monitor():
    result = SignalMonitor().update("BULLISH", 110, 100, 90, 110, .9)
    assert result.state == SignalState.TARGET_REACHED


def test_authentication():
    auth = RequestAuthenticator("secret")
    sig = auth.sign("job")
    assert auth.verify("job", sig).authenticated


def test_event_gate():
    event = MarketEvent("x", 110, "event", EventImpact.HIGH)
    assert EventRiskGate().blocked((event,), 100, 20)
