from market_runtime.contracts import Candle
from research.replay import MarketReplay,ResearchSplitter,WalkForward
from research.backtest import BacktestEngine,Trade
from research.monte_carlo import MonteCarlo

def cs(): return [Candle(i,10,12,8,11) for i in range(10)]
def test_replay_is_causal():
    frames=list(MarketReplay().replay(cs(),1)); assert all(f.candles[-1].timestamp==f.index for f in frames)
def test_split_and_walkforward():
    s=ResearchSplitter().split(cs()); assert len(s.train)+len(s.validation)+len(s.test)==10
    assert list(WalkForward().windows(cs(),4,2))
def test_backtest():
    r=BacktestEngine().run(cs(),[Trade('BUY',10,8,12)]); assert r.trades==1
def test_monte_carlo(): assert MonteCarlo().simulate([1,-1],10).trials==10
