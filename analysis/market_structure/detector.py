from __future__ import annotations

from analysis.market_structure.models import (
    SwingPoint,
    MarketStructureResult,
)


class MarketStructureDetector:
    """
    Detect market structure.

    Detects:
    - Higher High (HH)
    - Higher Low (HL)
    - Lower High (LH)
    - Lower Low (LL)
    - Trend
    - BOS
    - CHoCH
    """

    def analyze(
        self,
        prices: list[float],
    ) -> MarketStructureResult:

        self._validate_prices(
            prices
        )

        swings = self._find_swings(
            prices
