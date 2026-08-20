from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class VWAPAnalyzer:
    """
    VWAP analysis engine.

    Calculates:
    - Session VWAP
    - Rolling VWAP
    - VWAP deviation
    - Price position relative to VWAP
    """

    def __init__(
        self,
        rolling_period: int = 20,
    ) -> None:

        if rolling_period < 2:
            raise ValueError(
                "rolling_period must be >= 2."
            )

        self.rolling_period = rolling_period

    @staticmethod
    def _validate(
        dataframe: pd.DataFrame,
    ) -> None:

        required = [
            "high",
            "low",
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

    @staticmethod
    def _typical_price(
        dataframe: pd.DataFrame,
    ) -> pd.Series:

        return (
            dataframe["high"]
            + dataframe["low"]
            + dataframe["close"]
        ) / 3.0

    def calculate_session_vwap(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.Series:

        self._validate(dataframe)

        typical_price = (
            self._typical_price(
                dataframe
            )
        )

        volume = dataframe["volume"]

        weighted_price = (
            typical_price * volume
        )

        cumulative_volume = (
            volume.cumsum()
        )

        cumulative_weighted_price = (
            weighted_price.cumsum()
        )

        return (
            cumulative_weighted_price
            / cumulative_volume.replace(
                0,
                np.nan,
            )
        )

    def calculate_rolling_vwap(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.Series:

        self._validate(dataframe)

        typical_price = (
            self._typical_price(
                dataframe
            )
        )

        volume = dataframe["volume"]

        weighted_price = (
            typical_price * volume
        )

        rolling_weighted_price = (
            weighted_price.rolling(
                self.rolling_period
            ).sum()
        )

        rolling_volume = (
            volume.rolling(
                self.rolling_period
            ).sum()
        )

        return (
            rolling_weighted_price
            / rolling_volume.replace(
                0,
                np.nan,
            )
        )

    def calculate_deviation(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.Series:

        self._validate(dataframe)

        vwap = (
            self.calculate_session_vwap(
                dataframe
            )
        )

        close = dataframe["close"]

        return (
            close - vwap
        )

    def calculate_percentage_deviation(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.Series:

        self._validate(dataframe)

        vwap = (
            self.calculate_session_vwap(
                dataframe
            )
        )

        close = dataframe["close"]

        return (
            (close - vwap)
            / vwap.replace(
                0,
                np.nan,
            )
        ) * 100.0

    def detect_position(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.Series:

        self._validate(dataframe)

        vwap = (
            self.calculate_session_vwap(
                dataframe
            )
        )

        close = dataframe["close"]

        position = pd.Series(
            "neutral",
            index=dataframe.index,
            dtype="object",
        )

        position.loc[
            close > vwap
        ] = "above_vwap"

        position.loc[
            close < vwap
        ] = "below_vwap"

        return position

    def detect_crossings(
        self,
        dataframe: pd.DataFrame,
    ) -> list[dict[str, Any]]:

        self._validate(dataframe)

        vwap = (
            self.calculate_session_vwap(
                dataframe
            )
        )

        close = dataframe["close"]

        crossings: list[
            dict[str, Any]
        ] = []

        for i in range(
            1,
            len(dataframe),
        ):

            previous_close = float(
                close.iloc[i - 1]
            )

            current_close = float(
                close.iloc[i]
            )

            previous_vwap = vwap.iloc[
                i - 1
            ]

            current_vwap = vwap.iloc[
                i
            ]

            if (
                pd.isna(previous_vwap)
                or pd.isna(current_vwap)
            ):
                continue

            crossed_up = (
                previous_close
                <= float(previous_vwap)
                and current_close
                > float(current_vwap)
            )

            crossed_down = (
                previous_close
                >= float(previous_vwap)
