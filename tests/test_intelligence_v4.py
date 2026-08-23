from analysis.mtf import MultiTimeframeEngine, TimeframeView
from analysis.style_selection import AnalysisMode, AnalysisStyle, StyleCatalog, StyleSelection
from analysis.weighting import EvidenceAggregator, WeightedEvidence
from core.conflict_gate import ConflictGate
from strategy.selection import StrategyCandidate, StrategySelector


def test_manual_style_selection_never_allows_unselected_style() -> None:
    selection = StyleSelection(AnalysisMode.MANUAL, ("price_action",))
    assert selection.allows("price_action")
    assert not selection.allows("elliott")


def test_hybrid_style_selection_adds_suggestions_without_duplicates() -> None:
    selection = StyleSelection(AnalysisMode.HYBRID, ("price_action",), ("volume", "price_action"))
    assert selection.effective_styles() == ("price_action", "volume")


def test_weighted_consensus_detects_conflict() -> None:
    result = EvidenceAggregator().aggregate((
        WeightedEvidence("a", "BUY", 1.0, 1.0, 1.0),
        WeightedEvidence("b", "SELL", 1.0, 1.0, 1.0),
    ))
    gate = ConflictGate(maximum_disagreement=0.4)
    decision = gate.evaluate(result)
    assert not decision.allowed


def test_mtf_engine_reports_alignment() -> None:
    result = MultiTimeframeEngine().evaluate(
        higher=(TimeframeView("4H", "BUY", 1.0),),
        middle=(TimeframeView("1H", "BUY", 0.8),),
        lower=(TimeframeView("15m", "SELL", 0.2),),
    )
    assert result.alignment > 0.0
    assert 0.0 <= result.conflict <= 1.0


def test_strategy_selector_prefers_higher_scored_eligible_candidates() -> None:
    result = StrategySelector().select((
        StrategyCandidate("a", 0.4),
        StrategyCandidate("b", 0.9),
        StrategyCandidate("c", 0.7, regime="range"),
    ), regime="trend", limit=2)
    assert result.selected == ("b", "a")


def test_style_catalog_rejects_unknown_style() -> None:
    catalog = StyleCatalog((AnalysisStyle("technical"),))
    assert catalog.names() == ("technical",)
    try:
        catalog.get("unknown")
    except KeyError:
        pass
    else:
        raise AssertionError("unknown style should be rejected")
