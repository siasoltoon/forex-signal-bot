from analysis.regime import MarketRegime, MarketRegimeEngine, RegimeEvidence
from analysis.scenario import ScenarioDirection, ScenarioEngine
from application.intelligence_flow import IntelligenceFlow


def test_regime_engine_selects_dominant_supported_regime() -> None:
    result = MarketRegimeEngine().classify(
        (
            RegimeEvidence("trend", 0.8),
            RegimeEvidence("range", 0.2),
        )
    )
    assert result.regime is MarketRegime.TREND
    assert result.confidence > 0.5


def test_regime_engine_never_invents_unknown_evidence() -> None:
    result = MarketRegimeEngine().classify((RegimeEvidence("future_regime", 1.0),))
    assert result.regime is MarketRegime.UNKNOWN


def test_scenario_engine_normalizes_probabilities() -> None:
    scenarios = ScenarioEngine().build(
        bullish_probability=2.0,
        bearish_probability=1.0,
        neutral_probability=1.0,
        bullish_condition="breakout_confirmed",
        bearish_condition="support_lost",
        neutral_condition="no_confirmation",
        bullish_invalidation="breakout_failed",
        bearish_invalidation="support_reclaimed",
        neutral_invalidation="directional_breakout",
    )
    assert scenarios[0].direction is ScenarioDirection.BULLISH
    assert abs(sum(item.probability for item in scenarios) - 1.0) < 1e-9


def test_intelligence_flow_blocks_invalid_data() -> None:
    regime = MarketRegimeEngine().classify((RegimeEvidence("trend", 1.0),))
    result = IntelligenceFlow().compose(
        data_valid=False,
        data_quality=1.0,
        regime=regime,
        decision_signal="BUY",
        decision_confidence=0.95,
    )
    assert result.no_trade
    assert result.decision_signal == "NO_TRADE"
    assert "invalid_data" in (result.no_trade_reason or "")


def test_intelligence_flow_blocks_unknown_regime_and_low_confidence() -> None:
    regime = MarketRegimeEngine().classify(())
    result = IntelligenceFlow().compose(
        data_valid=True,
        data_quality=0.9,
        regime=regime,
        decision_signal="BUY",
        decision_confidence=0.2,
    )
    assert result.no_trade
    assert "unknown_market_regime" in (result.no_trade_reason or "")
    assert "low_confidence" in (result.no_trade_reason or "")


def test_intelligence_flow_preserves_valid_decision() -> None:
    regime = MarketRegimeEngine().classify((RegimeEvidence("trend", 1.0),))
    result = IntelligenceFlow().compose(
        data_valid=True,
        data_quality=0.95,
        regime=regime,
        decision_signal="SELL",
        decision_confidence=0.8,
    )
    assert not result.no_trade
    assert result.decision_signal == "SELL"
