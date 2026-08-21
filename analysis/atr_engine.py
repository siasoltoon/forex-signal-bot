from __future__ import annotations

from dataclasses import dataclass



# ==================================================
# ATR Result
# ==================================================

@dataclass(
    frozen=True
)
class ATRResult:
    """
    ATR calculation result.

    Contains:
    - Current ATR value
    - ATR percentage
    - Volatility state
    """


    atr: float


    atr_percentage: float


    volatility: str



# ==================================================
# ATR Engine
# ==================================================

class ATREngine:
    """
    Calculates Average True Range.

    Used for:
    - Dynamic Stop Loss
    - Volatility detection
    - Risk management
    """



    def __init__(
        self,
        period: int = 14,
    ) -> None:


        self.period = period



    # ==================================================
    # True Range
    # ==================================================

    @staticmethod
    def true_range(
        prices: list[float],
    ) -> list[float]:


        if len(prices) < 2:

            return []


        ranges = []


        for i in range(
            1,
            len(prices)
        ):


            high = prices[i]


            low = prices[i]


            previous_close = prices[i - 1]


            tr = max(

                high - low,


                abs(
                    high - previous_close
                ),


                abs(
                    low - previous_close
                )

            )


            ranges.append(tr)



        return ranges



    # ==================================================
    # ATR Calculation
    # ==================================================

    def calculate(
        self,
        prices: list[float],
    ) -> ATRResult:


        if len(prices) <= self.period:

            return ATRResult(

                atr=0.0,

                atr_percentage=0.0,

                volatility="unknown",

            )



        ranges = self.true_range(
            prices
        )



        recent_ranges = ranges[

            -self.period:

        ]



        atr = sum(

            recent_ranges

        ) / len(

            recent_ranges

        )



        current_price = prices[-1]



        if current_price == 0:

            atr_percentage = 0.0


        else:

            atr_percentage = (

                atr

                /

                current_price

            ) * 100



        volatility = self.classify_volatility(

            atr_percentage

        )



        return ATRResult(

            atr=round(

                atr,

                6

            ),


            atr_percentage=round(

                atr_percentage,

                3

            ),


            volatility=volatility,

        )



    # ==================================================
    # Volatility Classification
    # ==================================================

    @staticmethod
    def classify_volatility(
        atr_percentage: float,
    ) -> str:


        if atr_percentage >= 3:

            return "HIGH"



        elif atr_percentage >= 1:

            return "MEDIUM"



        elif atr_percentage > 0:

            return "LOW"



        return "UNKNOWN"
