from __future__ import annotations

from analysis.market_structure.models import (
    SwingPoint,
    MarketStructureResult,
)


class MarketStructureDetector:
    """
    Detect basic market structure.

    Detects:
    - Higher High (HH)
    - Higher Low (HL)
    - Lower High (LH)
    - Lower Low (LL)
    - Trend direction
    - BOS
    - CHoCH
    """


    def analyze(
        self,
        prices: list[float],
    ) -> MarketStructureResult:
        """
        Analyze price structure.
        """

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


        previous = prices[0]


        for index in range(
            1,
            len(prices) - 1,
        ):

            current = prices[index]

            next_price = prices[
                index + 1
            ]


            if (
                current > previous
                and current > next_price
            ):
                swings.append(
                    SwingPoint(
                        index=index,
                        price=current,
                        kind="HH",
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
                        kind="LL",
                    )
                )


            previous = current


        return swings



    @staticmethod
    def _detect_trend(
        swings: list[SwingPoint],
    ) -> str:

        if len(swings) < 2:
            return "unknown"


        last = swings[-1]

        previous = swings[-2]


        if (
            last.price > previous.price
        ):
            return "bullish"


        if (
            last.price < previous.price
        ):
            return "bearish"


        return "sideways"



    @staticmethod
    def _detect_bos(
        swings: list[SwingPoint],
    ) -> bool:

        if len(swings) < 3:
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


        first = swings[-3]

        second = swings[-2]

        third = swings[-1]


        return (
            first.price < second.price
            and third.price < second.price
        )
