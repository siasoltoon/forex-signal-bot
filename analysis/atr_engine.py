
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Sequence


# ==================================================
# ATR Result
# ==================================================

@dataclass(
    frozen=True
)
class ATRResult:
    """
    Professional ATR calculation result.

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
    Professional Average True Range engine.

    Features:

    - True Range calculation
    - Wilder ATR smoothing
    - ATR percentage
    - Volatility classification
    - OHLC-aware calculation
    - Close-only fallback
    - Input validation
    - Safe handling of insufficient data

    Supported inputs:

    1. list[float]
       Example:
           [100.0, 101.2, 99.8, 102.0]

    2. Candle-like objects
       Objects containing:
           high
           low
           close

    The engine remains compatible with the existing
    FullAnalysisEngine API.
    """

    def __init__(
        self,
        period: int = 14,
        low_volatility_threshold: float = 0.5,
        medium_volatility_threshold: float = 1.5,
        high_volatility_threshold: float = 3.0,
    ) -> None:

        if period <= 0:
            raise ValueError(
                "ATR period must be greater than zero."
            )

        if (
            low_volatility_threshold < 0
            or medium_volatility_threshold < 0
            or high_volatility_threshold < 0
        ):
            raise ValueError(
                "Volatility thresholds cannot be negative."
            )

        if not (
            low_volatility_threshold
            <= medium_volatility_threshold
            <= high_volatility_threshold
        ):
            raise ValueError(
                "Volatility thresholds must be ordered "
                "from low to high."
            )

        self.period = period

        self.low_volatility_threshold = (
            low_volatility_threshold
        )

        self.medium_volatility_threshold = (
            medium_volatility_threshold
        )

        self.high_volatility_threshold = (
            high_volatility_threshold
        )

    # ==================================================
    # Numeric Validation
    # ==================================================

    @staticmethod
    def _is_valid_number(
        value: Any,
    ) -> bool:
        """
        Checks whether a value is a valid finite number.
        """

        try:
            return isfinite(
                float(value)
            )
        except (
            TypeError,
            ValueError,
        ):
            return False

    # ==================================================
    # Normalize Price Input
    # ==================================================

    @classmethod
    def _normalize_prices(
        cls,
        prices: Sequence[Any],
    ) -> list[float]:
        """
        Converts close-price input into a clean
        list of finite floats.
        """

        normalized: list[float] = []

        for value in prices:

            if cls._is_valid_number(value):

                price = float(value)

                if price > 0:
                    normalized.append(price)

        return normalized

    # ==================================================
    # Extract OHLC
    # ==================================================

    @classmethod
    def _extract_ohlc(
        cls,
        data: Sequence[Any],
    ) -> tuple[
        list[float],
        list[float],
        list[float],
    ]:
        """
        Extracts high, low and close from Candle-like
        objects.

        Returns:

            highs
            lows
            closes

        Raises:

            ValueError
                If OHLC data is invalid.
        """

        highs: list[float] = []

        lows: list[float] = []

        closes: list[float] = []

        for item in data:

            high = getattr(
                item,
                "high",
                None,
            )

            low = getattr(
                item,
                "low",
                None,
            )

            close = getattr(
                item,
                "close",
                None,
            )

            if not (
                cls._is_valid_number(high)
                and cls._is_valid_number(low)
                and cls._is_valid_number(close)
            ):
                raise ValueError(
                    "Invalid OHLC candle data."
                )

            high_value = float(high)

            low_value = float(low)

            close_value = float(close)

            if (
                high_value <= 0
                or low_value <= 0
                or close_value <= 0
            ):
                raise ValueError(
                    "OHLC prices must be greater than zero."
                )

            if high_value < low_value:
                raise ValueError(
                    "Candle high cannot be lower than low."
                )

            if not (
                low_value
                <= close_value
                <= high_value
            ):
                raise ValueError(
                    "Candle close must be between "
                    "low and high."
                )

            highs.append(high_value)

            lows.append(low_value)

            closes.append(close_value)

        return (
            highs,
            lows,
            closes,
        )

    # ==================================================
    # True Range
    # ==================================================

    @staticmethod
    def true_range(
        prices: list[float],
    ) -> list[float]:
        """
        Calculates True Range from close-only prices.

        Since high and low are unavailable in this mode,
        absolute close-to-close movement is used.

        This method is preserved for backward compatibility.
        """

        if len(prices) < 2:
            return []

        ranges: list[float] = []

        for i in range(1, len(prices)):

            current_price = float(
                prices[i]
            )

            previous_close = float(
                prices[i - 1]
            )

            tr = abs(
                current_price
                - previous_close
            )

            ranges.append(tr)

        return ranges

    # ==================================================
    # OHLC True Range
    # ==================================================

    @staticmethod
    def ohlc_true_range(
        highs: list[float],
        lows: list[float],
        closes: list[float],
    ) -> list[float]:
        """
        Calculates standard True Range using OHLC data.

        Formula:

            TR = max(
                High - Low,
                abs(High - Previous Close),
                abs(Low - Previous Close)
            )
        """

        if not (
            len(highs)
            == len(lows)
            == len(closes)
        ):
            raise ValueError(
                "OHLC arrays must have equal length."
            )

        if len(closes) < 2:
            return []

        ranges: list[float] = []

        for i in range(1, len(closes)):

            high = highs[i]

            low = lows[i]

            previous_close = closes[i - 1]

            current_range = max(
                high - low,
                abs(
                    high
                    - previous_close
                ),
                abs(
                    low
                    - previous_close
                ),
            )

            ranges.append(
                max(
                    0.0,
                    current_range,
                )
            )

        return ranges

    # ==================================================
    # Wilder ATR
    # ==================================================

    def _wilder_atr(
        self,
        true_ranges: list[float],
    ) -> float:
        """
        Calculates ATR using Wilder smoothing.

        Initial ATR:

            SMA(TR, period)

        Subsequent ATR:

            ATR =
                (
                    previous ATR * (period - 1)
                    + current TR
                )
                / period
        """

        if len(true_ranges) < self.period:
            return 0.0

        initial_window = true_ranges[
            : self.period
        ]

        atr = (
            sum(initial_window)
            / self.period
        )

        for current_tr in true_ranges[
            self.period:
        ]:

            atr = (
                (
                    atr
                    * (self.period - 1)
                )
                + current_tr
            ) / self.period

        return max(
            0.0,
            atr,
        )



    # ==================================================
    # Volatility Classification
    # ==================================================

    @staticmethod
    def classify_volatility(
        atr_percentage: float,
    ) -> str:
        """
        Classifies market volatility from ATR percentage.

        Returns:

        - VERY_LOW
        - LOW
        - MEDIUM
        - HIGH
        """

        if atr_percentage <= 0:
            return "UNKNOWN"

        if atr_percentage < 0.5:
            return "VERY_LOW"

        if atr_percentage < 1.5:
            return "LOW"

        if atr_percentage < 3.0:
            return "MEDIUM"

        return "HIGH"

    # ==================================================
    # ATR Percentage
    # ==================================================

    @staticmethod
    def calculate_atr_percentage(
        atr: float,
        current_price: float,
    ) -> float:
        """
        Converts ATR into percentage of current price.
        """

        if (
            atr <= 0
            or current_price <= 0
        ):
            return 0.0

        return (
            atr
            / current_price
        ) * 100.0

    # ==================================================
    # Empty Result
    # ==================================================

    @staticmethod
    def _empty_result() -> ATRResult:
        """
        Returns a safe result when there is not enough data.
        """

        return ATRResult(
            atr=0.0,
            atr_percentage=0.0,
            volatility="UNKNOWN",
        )

    # ==================================================
    # Main Calculation
    # ==================================================

    def calculate(
        self,
        prices: Sequence[Any],
    ) -> ATRResult:
        """
        Calculates the current ATR.

        The method automatically detects whether the
        input contains:

        - Candle/OHLC objects
        - Close-only prices

        Close-only data uses absolute price movement
        because high/low information is unavailable.
        """

        if prices is None:
            return self._empty_result()

        if len(prices) == 0:
            return self._empty_result()

        # ==================================================
        # OHLC Mode
        # ==================================================

        first_item = prices[0]

        has_ohlc = (
            hasattr(first_item, "high")
            and hasattr(first_item, "low")
            and hasattr(first_item, "close")
        )

        if has_ohlc:

            highs, lows, closes = (
                self._extract_ohlc(
                    prices
                )
            )

            if len(closes) <= self.period:
                return self._empty_result()

            true_ranges = (
                self.ohlc_true_range(
                    highs,
                    lows,
                    closes,
                )
            )

            atr = self._wilder_atr(
                true_ranges
            )

            current_price = closes[-1]

        # ==================================================
        # Close-Only Mode
        # ==================================================

        else:

            normalized = (
                self._normalize_prices(
                    prices
                )
            )

            if len(normalized) <= self.period:
                return self._empty_result()

            true_ranges = (
                self.true_range(
                    normalized
                )
            )

            atr = self._wilder_atr(
                true_ranges
            )

            current_price = normalized[-1]

        # ==================================================
        # ATR Percentage
        # ==================================================

        atr_percentage = (
            self.calculate_atr_percentage(
                atr=atr,
                current_price=current_price,
            )
        )

        # ==================================================
        # Volatility
        # ==================================================

        volatility = (
            self.classify_volatility(
                atr_percentage
            )
        )

        # ==================================================
        # Result
        # ==================================================

        return ATRResult(
            atr=round(
                atr,
                6,
            ),
            atr_percentage=round(
                atr_percentage,
                3,
            ),
            volatility=volatility,
        )



