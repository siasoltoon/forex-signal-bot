from __future__ import annotations

from dataclasses import dataclass



@dataclass(
    frozen=True
)
class PriceZone:
    """
    Represents supply or demand zone.
    """

    zone_type: str
    # supply / demand

    high: float

    low: float

    strength: float

    touches: int

    fresh: bool



@dataclass(
    frozen=True
)
class SupplyDemandResult:
    """
    Supply and demand analysis result.
    """

    supply_zones: list[PriceZone]

    demand_zones: list[PriceZone]
