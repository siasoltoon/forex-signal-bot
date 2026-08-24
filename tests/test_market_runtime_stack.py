from market_runtime.contracts import Candle
from market_runtime.cache import TTLCache
from market_runtime.quality import DataQualityPipeline

def candles(): return [Candle(1,10,12,9,11),Candle(2,11,13,10,12)]
def test_quality_valid(): assert DataQualityPipeline().validate(candles()).valid
def test_quality_rejects_bad_ohlc():
    bad=[Candle(1,10,9,8,9)]
    assert not DataQualityPipeline().validate(bad).valid
def test_cache():
    c=TTLCache(); c.put('x',1,10); assert c.get('x')==1
