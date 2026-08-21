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
        )

        trend = self._detect_trend(
            swings
        )

        bos = self._detect_bos(
            swings
        )

        choch = self._detect_choch(
            swings
        )

        return MarketStructureResult(
            trend=trend,
            swings=swings,
            bos=bos,
            choch=choch,
        )


    @staticmethod
    def _validate_prices(
        prices: list[float],
    ) -> None:

        if not isinstance(
            prices,
            list,
        ):
            raise TypeError(
                "prices must be a list."
            )

        if len(prices) < 3:
            raise ValueError(
                "At least 3 prices are required."
            )


    @staticmethod
    def _find_swings(
        prices: list[float],
    ) -> list[SwingPoint]:

        swings: list[SwingPoint] = []

        for index in range(
            1,
            len(prices) - 1,
        ):

            previous = prices[index - 1]
            current = prices[index]
            next_price = prices[index + 1]


            if (
                current > previous
                and current > next_price
            ):
                swings.append(
                    SwingPoint(
                        index=index,
                        price=current,
                        kind="HIGH",
                    )
                )


            elif (
                current < previous
                and current < next_price
            ):
                swings.append(
                    SwingPoint(
                        index=index,
                        price=current,
                        kind="LOW",
                    )
                )


        return swings



    @staticmethod
    def _detect_trend(
        swings: list[SwingPoint],
    ) -> str:

        highs = [
            swing.price
            for swing in swings
            if swing.kind == "HIGH"
        ]

        lows = [
            swing.price
            for swing in swings
            if swing.kind == "LOW"
        ]


        if len(highs) >= 2:

            if highs[-1] > highs[-2]:
                return "bullish"


            if highs[-1] < highs[-2]:
                return "bearish"


        if len(lows) >= 2:

            if lows[-1] > lows[-2]:
                return "bullish"


            if lows[-1] < lows[-2]:
                return "bearish"


        return "unknown"



    @staticmethod
    def _detect_bos(
        swings: list[SwingPoint],
    ) -> bool:

        if len(swings) < 2:
            return False

        return (
            swings[-1].price
            >
            swings[-2].price
        )



    @staticmethod
    def _detect_choch(
        swings: list[SwingPoint],
    ) -> bool:

        if len(swings) < 3:
            return False

        return (
            swings[-3].price
            <
            swings[-2].price
            and
            swings[-1].price
            <
            swings[-2].price
        )
