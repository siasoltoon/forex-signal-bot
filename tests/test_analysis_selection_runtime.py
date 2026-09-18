from __future__ import annotations

from dataclasses import dataclass

from analysis.multitimeframe import MultiTimeframeEngine, TimeframeEvidence, TimeframeRole
from analysis.plugins import AnalyzerRegistry, PluginDescriptor, PluginStatus
from analysis.regime import MarketRegime, RegimeEngine, RegimeEvidence
from analysis.selection import AnalysisMode, AnalysisSelection, PresetStore, validate_selection
from analysis.style_catalog import enabled_catalog
from analysis.style_selector import StyleSelector


@dataclass(frozen=True)
class FakePlugin:
    key: str = "fake"
    name: str = "Fake"
    status: PluginStatus = PluginStatus.ENABLED

    def analyze(self, context):
        raise NotImplementedError


def test_registry_rejects_duplicate_plugin() -> None:
    registry = AnalyzerRegistry()
    registry.register(FakePlugin(), PluginDescriptor("fake", "Fake", "test", "test"))
    try:
        registry.register(FakePlugin())
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate plugin was accepted")


def test_manual_selection_never_adds_hidden_styles() -> None:
    selection = AnalysisSelection(AnalysisMode.MANUAL, ("technical",))
    selector = StyleSelector(enabled_catalog())
    assert selector.resolve(selection, MarketRegime.TREND) == ("technical",)


def test_smart_selection_uses_regime_suggestions() -> None:
    selection = AnalysisSelection(AnalysisMode.SMART)
    selector = StyleSelector(enabled_catalog())
    assert selector.resolve(selection, MarketRegime.TREND) == (
        "technical", "price_action", "market_structure", "momentum"
    )


def test_hybrid_selection_merges_without_duplicates() -> None:
    selection = AnalysisSelection(
        AnalysisMode.HYBRID,
        ("technical",),
        ("technical", "momentum"),
    )
    assert selection.effective_styles() == ("technical", "momentum")


def test_preset_store_round_trip() -> None:
    store = PresetStore()
    selection = AnalysisSelection(AnalysisMode.MANUAL, ("technical",))
    store.save("my preset", selection)
    assert store.get("my preset") == selection
    assert store.names() == ("my preset",)
    store.delete("my preset")
    assert store.names() == ()


def test_regime_engine_prefers_highest_valid_confidence() -> None:
    engine = RegimeEngine()
    result = engine.select(
        (
            RegimeEvidence(MarketRegime.RANGE, 0.4, "range"),
            RegimeEvidence(MarketRegime.TREND, 0.8, "trend"),
        )
    )
    assert result == MarketRegime.TREND


def test_multitimeframe_detects_conflict() -> None:
    result = MultiTimeframeEngine().evaluate(
        (
            TimeframeEvidence("4H", TimeframeRole.CONTEXT, "BULLISH", 0.9),
            TimeframeEvidence("1H", TimeframeRole.STRUCTURE, "BEARISH", 0.8),
        )
    )
    assert result.aligned is False
    assert result.conflict_score == 0.5


def test_selection_rejects_unknown_styles() -> None:
    try:
        validate_selection(AnalysisSelection(AnalysisMode.MANUAL, ("unknown",)), {"technical"})
    except ValueError as exc:
        assert "unknown" in str(exc)
    else:
        raise AssertionError("unknown style was accepted")
