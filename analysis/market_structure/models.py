from __future__ import annotations

from dataclasses import dataclass



@dataclass(
    frozen=True
)
class SwingPoint:
    """
    Represents a market swing point.
    """

    index: int

    price: float

    kind: str
    # HH / HL / LH / LL



@dataclass(
    frozen=True
)
class MarketStructureResult:
    """
    Market structure analysis result.
    """

    trend: str

    swings: list[SwingPoint]

    bos: bool

    choch: bool
