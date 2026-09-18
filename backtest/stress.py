from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StressScenario:
    name: str
    fee_multiplier: float = 1.0
    slippage_multiplier: float = 1.0
    pnl_multiplier: float = 1.0


@dataclass(frozen=True, slots=True)
class StressResult:
    scenario: str
    adjusted_pnl: float


class StressTester:
    def run(self, base_pnl: float, scenario: StressScenario) -> StressResult:
        if scenario.fee_multiplier < 0 or scenario.slippage_multiplier < 0 or scenario.pnl_multiplier < 0:
            raise ValueError("stress multipliers must be non-negative")
        adjustment = scenario.fee_multiplier + scenario.slippage_multiplier - 2.0
        adjusted = base_pnl * scenario.pnl_multiplier - abs(base_pnl) * max(0.0, adjustment) * 0.5
        return StressResult(scenario.name, adjusted)
