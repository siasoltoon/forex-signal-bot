from __future__ import annotations

from dataclasses import dataclass

from analysis.contracts import AnalysisContext
from analysis.plugin_runtime_v3 import AnalysisPluginRuntime, PluginRun
from analysis.regime_policy_v2 import MarketRegime, RegimePolicyBook
from analysis.selection import AnalysisMode, AnalysisSelection


@dataclass(frozen=True, slots=True)
class RuntimePlan:
    selection: AnalysisSelection
    regime: MarketRegime
    effective_styles: tuple[str, ...]


class IntelligenceRuntimeV2:
    """Coordinates selection, regime policy, and isolated plugin execution."""

    def __init__(self, plugins: AnalysisPluginRuntime, policies: RegimePolicyBook | None = None) -> None:
        self.plugins = plugins
        self.policies = policies or RegimePolicyBook()

    def plan(self, selection: AnalysisSelection, regime: MarketRegime) -> RuntimePlan:
        requested = selection.effective_styles()
        if selection.mode == AnalysisMode.SMART:
            requested = self.policies.suggestions(regime)
        allowed = self.policies.allowed(regime, tuple(requested))
        return RuntimePlan(
            selection=selection,
            regime=regime,
            effective_styles=tuple(dict.fromkeys(allowed)),
        )

    def run(self, context: AnalysisContext, selection: AnalysisSelection, regime: MarketRegime) -> tuple[RuntimePlan, PluginRun]:
        plan = self.plan(selection, regime)
        effective = AnalysisSelection(mode=AnalysisMode.MANUAL, styles=plan.effective_styles)
        return plan, self.plugins.run(context, effective)
