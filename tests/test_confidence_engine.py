from analysis.confidence_engine import (
    ConfidenceEngine,
)



class MockAnalysis:
    """
    Fake analysis object
    for testing confidence engine.
    """

    smart_money_score = 80

    structure_score = 75

    price_action_score = 70

    momentum_score = 65

    elliott_score = 60

    harmonic_score = 55

    wyckoff_score = 50



def test_confidence_engine_returns_result():

    engine = ConfidenceEngine()


    result = engine.evaluate(

        MockAnalysis()

    )


    assert result.confidence >= 0

    assert result.confidence <= 1



def test_confidence_engine_counts_votes():

    engine = ConfidenceEngine()


    result = engine.evaluate(

        MockAnalysis()

    )


    assert result.bullish_votes >= 1



def test_confidence_engine_detects_conflict():


    class ConflictAnalysis:


        smart_money_score = 90

        structure_score = 85

        price_action_score = 80

        momentum_score = 75

        elliott_score = 20

        harmonic_score = 15

        wyckoff_score = 10



    engine = ConfidenceEngine()


    result = engine.evaluate(

        ConflictAnalysis()

    )


    assert (

        len(result.warnings)

        >

        0

    )
