from analysis.decision_engine import (
    DecisionEngine,
    DecisionResult,
)



class MockAnalysis:
    """
    Fake analysis object
    for testing DecisionEngine.
    """

    smart_money_score = 90

    structure_score = 80

    price_action_score = 70

    trend_score = 60

    momentum_score = 75


    elliott_score = 50

    harmonic_score = 50

    wyckoff_score = 50


    smc_bias = "bullish"



def test_decision_engine_returns_result():

    engine = DecisionEngine()

    result = engine.decide(
        MockAnalysis()
    )


    assert isinstance(
        result,
        DecisionResult
    )



def test_decision_engine_has_signal():

    engine = DecisionEngine()

    result = engine.decide(
        MockAnalysis()
    )


    assert result.signal in [

        "STRONG BUY",

        "BUY",

        "NEUTRAL",

        "SELL",

        "STRONG SELL",

    ]



def test_decision_engine_confidence_range():

    engine = DecisionEngine()

    result = engine.decide(
        MockAnalysis()
    )


    assert 0 <= result.confidence <= 100



def test_bullish_bias():

    engine = DecisionEngine()

    result = engine.decide(
        MockAnalysis()
    )


    assert result.bias == "bullish"
