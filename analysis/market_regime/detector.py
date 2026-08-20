from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class MarketRegime:
    index: Any
    regime: str
    trend: str
    volatility: str
    trend_strength: float
    volatility_score: float
    confidence: float


class MarketRegimeDetector:
    """
    Detects the current market regime.

    Regimes:
    - trending_up
    - trending_down
    - ranging
    - high_volatility
    - low_volatility
    - transition

    The detector is designed as a context layer.
    It does not generate trading signals.
    """

    def __init__(
        self,
        trend_period: int = 50,
        volatility_period: int = 20,
        trend_threshold: float = 0.003,
        high_volatility_multiplier: float = 1.5,
        low_volatility_multiplier: float = 0.6,
    ) -> None:

        if trend_period < 5:
            raise ValueError(
                "trend_period must be >= 5."
            )

        if volatility_period < 5:
            raise ValueError(
                "volatility_period must be >= 5."
            )

        if trend_threshold < 0:
            raise ValueError(
                "trend_threshold must be >= 0."
            )

        if high_volatility_multiplier <= 1:
            raise ValueError(
                "high_volatility_multiplier must be > 1."
            )

        if not 0 < low_volatility_multiplier < 1:
            raise ValueError(
                "low_volatility_multiplier must be between 0 and 1."
            )

        self.trend_period = trend_period
        self.volatility_period = volatility_period
        self.trend_threshold = trend_threshold
        self.high_volatility_multiplier = (
            high_volatility_multiplier
        )
        self.low_volatility_multiplier = (
            low_volatility_multiplier
        )

    @staticmethod
    def _validate(
        dataframe: pd.DataFrame,
    ) -> None:

        required = [
            "high",
            "low",
            "close",
        ]

        missing = [
            column
            for column in required
            if column not in dataframe.columns
        ]

        if missing:
            raise ValueError(
                f"Missing columns: {missing}"
            )

        if dataframe.empty:
            raise ValueError(
                "DataFrame cannot be empty."
            )

    def _returns(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.Series:

        return dataframe[
            "close"
        ].pct_change()

    def _realized_volatility(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.Series:

        returns = self._returns(
            dataframe
        )

        return returns.rolling(
            self.volatility_period
        ).std()

    def _atr(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.Series:

        high = dataframe["high"]
        low = dataframe["low"]
        close = dataframe["close"]

        previous_close = close.shift(1)

        true_range = pd.concat(
            [
                high - low,
                (
                    high
                    - previous_close
                ).abs(),
                (
                    low
                    - previous_close
                ).abs(),
            ],
            axis=1,
        ).max(axis=1)

        return true_range.rolling(
            self.volatility_period
        ).mean()

    def _trend_strength(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.Series:

        close = dataframe["close"]

        previous = close.shift(
            self.trend_period
        )

        strength = (
            (close - previous)
            / previous.abs()
        )

        return strength

    def _classify_trend(
        self,
        strength: float,
    ) -> str:

        if strength > self.trend_threshold:
            return "bullish"

        if strength < -self.trend_threshold:
            return "bearish"

        return "neutral"

    def _classify_volatility(
        self,
        current_volatility: float,
        average_volatility: float,
    ) -> str:

        if (
            average_volatility <= 0
            or not np.isfinite(
                average_volatility
            )
        ):
            return "normal"

        ratio = (
            current_volatility
            / average_volatility
        )

        if (
            ratio
            >= self.high_volatility_multiplier
        ):
            return "high"

        if (
            ratio
            <= self.low_volatility_multiplier
        ):
            return "low"

        return "normal"

    def detect(
        self,
        dataframe: pd.DataFrame,
    ) -> list[MarketRegime]:

        self._validate(dataframe)

        trend_strength = (
            self._trend_strength(
                dataframe
            )
        )

        volatility = (
            self._realized_volatility(
                dataframe
            )
        )

        average_volatility = (
            volatility.rolling(
                self.volatility_period
            ).mean()
        )

        results: list[
            MarketRegime
        ] = []

        for i in range(
            len(dataframe)
        ):

            strength_value = (
                trend_strength.iloc[i]
            )

            volatility_value = (
                volatility.iloc[i]
            )

            average_value = (
                average_volatility.iloc[i]
            )

            if pd.isna(
                strength_value
            ):
                strength = 0.0
                trend = "neutral"
            else:
                strength = float(
                    strength_value
                )

                trend = (
                    self._classify_trend(
                        strength
                    )
                )

            if (
                pd.isna(
                    volatility_value
                )
                or pd.isna(
                    average_value
                )
            ):
                volatility_state = (
                    "normal"
                )

                volatility_score = 0.0

            else:
                volatility_state = (
                    self._classify_volatility(
                        float(
                            volatility_value
                        ),
                        float(
                            average_value
                        ),
                    )
                )

                volatility_score = (
                    float(
                        volatility_value
                    )
                    / max(
                        float(
                            average_value
                        ),
                        1e-12,
                    )
                )

            if (
                trend == "bullish"
                and volatility_state
                != "high"
            ):

                regime = "trending_up"

            elif (
                trend == "bearish"
                and volatility_state
                != "high"
            ):

                regime = "trending_down"

            elif (
                volatility_state
                == "high"
            ):

                regime = "high_volatility"

            elif (
                volatility_state
                == "low"
                and trend == "neutral"
            ):

                regime = "low_volatility"

            elif trend == "neutral":

                regime = "ranging"

            else:

                regime = "transition"

            trend_confidence = min(
                1.0,
                abs(strength)
                / max(
                    self.trend_threshold,
                    1e-12,
                ),
            )

            volatility_confidence = min(
                1.0,
                abs(
                    volatility_score
                    - 1.0
                ),
            )

            confidence = (
                trend_confidence * 0.6
                + volatility_confidence * 0.4
            )

            results.append(
                MarketRegime(
                    index=dataframe.index[i],
                    regime=regime,
                    trend=trend,
                    volatility=volatility_state,
                    trend_strength=round(
                        strength,
                        6,
                    ),
                    volatility_score=round(
                        volatility_score,
                        4,
                    ),
                    confidence=round(
                        min(
                            1.0,
                            confidence,
                        ),
                        4,
                    ),
                )
            )

        return results

    def current(
        self,
        dataframe: pd.DataFrame,
    ) -> MarketRegime:

        regimes = self.detect(
            dataframe
        )

        if not regimes:
            raise ValueError(
                "Unable to determine market regime."
            )

        return regimes[-1]

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        self._validate(dataframe)

        regimes = self.detect(
            dataframe
        )

        current = regimes[-1]

        regime_counts: dict[
            str,
            int,
        ] = {}

        for item in regimes:

            regime_counts[
                item.regime
            ] = (
                regime_counts.get(
                    item.regime,
                    0,
                )
                + 1
            )

        return {
            "current": current,
            "regimes": regimes,
            "regime_counts":
                regime_counts,
        }
