from __future__ import annotations

from analysis.plugins import PluginDescriptor
from analysis.regime import MarketRegime
from analysis.selection import AnalysisMode, AnalysisSelection


DEFAULT_REGIME_STYLES: dict[MarketRegime, tuple[str, ...]] = {
    MarketRegime.TREND: ("technical", "price_action", "market_structure", "momentum"),
    MarketRegime.RANGE: ("technical", "price_action", "support_resistance"),
    MarketRegime.BREAKOUT: ("breakout", "volume", "market_structure"),
    MarketRegime.HIGH_VOLATILITY: ("volatility", "market_structure", "risk"),
    MarketRegime.LOW_VOLATILITY: ("volatility", "range"),
    MarketRegime.ACCUMULATION: ("wyckoff", "volume", "market_structure"),
    MarketRegime.DISTRIBUTION: ("wyckoff", "volume", "market_structure"),
    MarketRegime.EXPANSION: ("breakout", "momentum", "volume"),
    MarketRegime.CONTRACTION: ("volatility", "range"),
    MarketRegime.CRISIS: (),
    MarketRegime.UNKNOWN: (),
}


class StyleSelector:
    def __init__(self, catalog: tuple[PluginDescriptor, ...]) -> None:
        self._available = {item.key for item in catalog if item.status.value == "ENABLED"}

    def suggest(self, regime: MarketRegime) -> tuple[str, ...]:
        return tuple(key for key in DEFAULT_REGIME_STYLES.get(regime, ()) if key in self._available)

    def resolve(self, selection: AnalysisSelection, regime: MarketRegime) -> tuple[str, ...]:
        suggestions = self.suggest(regime)
        effective = selection.effective_styles() if selection.mode != AnalysisMode.SMART else suggestions
        return tuple(key for key in effective if key in self._available)
