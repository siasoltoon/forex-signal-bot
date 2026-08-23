from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class ExposureReport:
    gross: float
    net: float
    concentration: float
    blocked: bool


class PortfolioExposureEngine:
    def assess(self, positions: Mapping[str, float], max_gross: float, max_net: float, max_single: float) -> ExposureReport:
        if max_gross <= 0 or max_net < 0 or max_single <= 0:
            raise ValueError("invalid exposure limits")
        gross = sum(abs(v) for v in positions.values())
        net = abs(sum(positions.values()))
        concentration = max((abs(v) / gross for v in positions.values()), default=0.0)
        blocked = gross > max_gross or net > max_net or concentration > max_single
        return ExposureReport(gross, net, concentration, blocked)
