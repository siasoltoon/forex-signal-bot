from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class VolumeIndicators:
    """
    Volume-based indicators.

    Includes:
    - OBV
    - Relative Volume
    - Volume SMA
    - Volume momentum
    - Volume trend
    """

    def __init__(
        self,
        volume_period: int = 20,
    ) -> None:

        if volume_period < 2:
            raise ValueError(
                "volume_period must be >= 2."
            )

        self.volume_period = volume_period

    @staticmethod
    def _validate(
        dataframe: pd.DataFrame,
    ) -> None:

        required = [
            "close",
            "volume",
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

    def obv(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.Series:

        self._validate(dataframe)

        close = dataframe["close"]
        volume = dataframe["volume"]

        direction = (
            close.diff()
            .fillna(0)
        )

        signed_volume = np.where(
            direction > 0,
            volume,
            np.where(
                direction < 0,
                -volume,
                0,
            ),
        )

        return pd.Series(
            signed_volume,
            index=dataframe.index,
        ).cumsum()

    def obv_sma(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.Series:

        self._validate(dataframe)

        obv = self.obv(
            dataframe
        )

        return obv.rolling(
            self.volume_period
        ).mean()

    def relative_volume(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.Series:

        self._validate(dataframe)

        volume = dataframe["volume"]

        average_volume = (
            volume.rolling(
                self.volume_period
            ).mean()
        )

        return (
            volume
            / average_volume.replace(
                0,
                np.nan,
            )
        )

    def volume_sma(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.Series:

        self._validate(dataframe)

        return dataframe[
            "volume"
        ].rolling(
            self.volume_period
        ).mean()

    def volume_momentum(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.Series:

        self._validate(dataframe)

        volume = dataframe["volume"]

        return (
            volume.pct_change(
                self.volume_period
            ) * 100.0
        )

    def volume_trend(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.Series:

        self._validate(dataframe)

        volume = dataframe["volume"]

        average = (
            volume.rolling(
                self.volume_period
            ).mean()
        )

        result = pd.Series(
            "normal",
            index=dataframe.index,
            dtype="object",
        )

        result.loc[
            volume
            > average * 1.5
        ] = "high"

        result.loc[
            volume
            < average * 0.5
        ] = "low"

        return result

    def detect_volume_divergence(
        self,
        dataframe: pd.DataFrame,
        lookback: int = 10,
    ) -> list[dict[str, Any]]:

        self._validate(dataframe)

        if lookback < 2:
            raise ValueError(
                "lookback must be >= 2."
            )

        obv = self.obv(
            dataframe
        )

        close = dataframe["close"]

        results: list[
            dict[str, Any]
        ] = []

        for i in range(
            lookback,
            len(dataframe),
        ):

            price_change = (
                float(close.iloc[i])
                - float(
                    close.iloc[
                        i - lookback
                    ]
                )
            )

            obv_change = (
                float(obv.iloc[i])
                - float(
                    obv.iloc[
                        i - lookback
                    ]
                )
            )

            bullish_divergence = (
                price_change < 0
                and obv_change > 0
            )

            bearish_divergence = (
                price_change > 0
                and obv_change < 0
            )

            if bullish_divergence:

                results.append(
                    {
                        "index":
                            dataframe.index[i],
                        "type":
                            "bullish_obv_divergence",
                        "price_change":
                            price_change,
                        "obv_change":
                            obv_change,
                    }
                )

            elif bearish_divergence:

                results.append(
                    {
                        "index":
                            dataframe.index[i],
                        "type":
                            "bearish_obv_divergence",
                        "price_change":
                            price_change,
                        "obv_change":
                            obv_change,
                    }
                )

        return results

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        self._validate(dataframe)

        obv = self.obv(
            dataframe
        )

        obv_sma = self.obv_sma(
            dataframe
        )

        relative_volume = (
            self.relative_volume(
                dataframe
            )
        )

        volume_sma = (
            self.volume_sma(
                dataframe
            )
        )

        momentum = (
            self.volume_momentum(
                dataframe
            )
        )

        trend = (
            self.volume_trend(
                dataframe
            )
        )

        divergence = (
            self.detect_volume_divergence(
                dataframe
            )
        )

        return {
            "obv": obv,
            "obv_sma": obv_sma,
            "relative_volume":
                relative_volume,
            "volume_sma":
                volume_sma,
            "volume_momentum":
                momentum,
            "volume_trend":
                trend,
            "divergence":
                divergence,
        }
