from engines.breakout import BreakoutEngine
from engines.candlestick import CandlestickEngine
from engines.confidence import ConfidenceEngine
from engines.timeframe_alignment import TimeframeAlignmentEngine
from engines.volatility import VolatilityEngine
from engines.wyckoff import WyckoffEngine


def test_candlestick_engine():
    result = CandlestickEngine().detect([1], [3], [0], [1])
    assert any(x.name == "DOJI" for x in result)


def test_breakout_engine():
    result = BreakoutEngine().analyze([2, 2, 2, 2, 2, 3], [0, 0, 0, 0, 0, 1], [1, 1, 1, 1, 1, 2.5])
    assert result.breakout is True


def test_wyckoff_engine():
    result = WyckoffEngine().classify([5, 4, 4, 5, 6, 7], [10, 10, 10, 20, 20, 30])
    assert result.phase in {"MARKUP", "MARKDOWN", "ACCUMULATION", "DISTRIBUTION", "RANGE"}


def test_volatility_engine():
    result = VolatilityEngine().analyze([100, 101, 99, 102, 101, 103, 102, 104, 103, 105, 104, 106])
    assert result.value >= 0


def test_timeframe_alignment():
    result = TimeframeAlignmentEngine().evaluate({"1D": "BULLISH", "4H": "BULLISH", "1H": "BEARISH"})
    assert result.dominant_direction == "BULLISH"


def test_confidence_blocks_low_quality():
    result = ConfidenceEngine().calculate(1, 0.2, 1, 0, 1)
    assert result.blocked is True
