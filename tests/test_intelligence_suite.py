from engines.analysis_fusion import AnalysisFusionEngine
from engines.market_regime import MarketRegimeEngine
from engines.market_structure import MarketStructureEngine
from engines.momentum import MomentumEngine
from engines.scenario_engine import ScenarioEngine
from engines.smc import SMCEngine
from engines.supply_demand import SupplyDemandEngine
from engines.volume_vwap import VolumeVWAPEngine


def test_structure_engine():
    result = MarketStructureEngine().analyze([1, 2, 3], [0, 1, 2])
    assert result.direction == "BULLISH"


def test_momentum_engine():
    result = MomentumEngine().analyze([1, 2, 3, 4, 5, 6])
    assert result.direction == "BULLISH"


def test_regime_engine():
    result = MarketRegimeEngine().classify([1, 2, 3, 4], [0.01, 0.01])
    assert result.regime == "TREND_UP"


def test_supply_demand_engine():
    assert SupplyDemandEngine().detect([3, 4, 5], [1, 2, 3])


def test_smc_engine():
    # Final candle sweeps the prior high (5 > 3) and closes back below it.
    result = SMCEngine().analyze([1, 2, 3, 5], [0, 1, 2, 1], [0.5, 1.5, 3.5, 4.0])
    assert result.liquidity_sweep is True
    assert result.direction == "BEARISH"


def test_volume_vwap_engine():
    result = VolumeVWAPEngine().analyze([2, 3], [0, 1], [1, 2], [10, 20])
    assert result.vwap > 0


def test_fusion_conflict_can_block():
    result = AnalysisFusionEngine().combine(["BULLISH", "BEARISH"], [1, 1])
    assert result.decision == "NO_TRADE"


def test_scenarios_normalize():
    scenarios = ScenarioEngine().build(0.4)
    assert abs(sum(s.probability for s in scenarios) - 1.0) < 1e-9
