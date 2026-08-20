from __future__ import annotations

import numpy as np
import pandas as pd


class IndicatorEngine:
    """
    Technical indicator calculation engine.

    This class calculates indicators only.
    Trading decisions are handled by higher-level
    analysis modules.
    """

    def __init__(
        self,
        dataframe: pd.DataFrame,
    ) -> None:

        self.df = dataframe.copy()

        required = [
            "open",
            "high",
            "low",
            "close",
        ]

        missing = [
            column
            for column in required
            if column not in self.df.columns
        ]

        if missing:
            raise ValueError(
                f"Missing columns: {missing}"
            )

        for column in required:
            self.df[column] = pd.to_numeric(
                self.df[column],
                errors="coerce",
            )

    # --------------------------------------------------
    # Moving averages
    # --------------------------------------------------

    def sma(
        self,
        period: int = 20,
    ) -> pd.Series:

        return self.df["close"].rolling(
            period
        ).mean()

    def ema(
        self,
        period: int = 20,
    ) -> pd.Series:

        return self.df["close"].ewm(
            span=period,
            adjust=False,
        ).mean()

    # --------------------------------------------------
    # RSI
    # --------------------------------------------------

    def rsi(
        self,
        period: int = 14,
    ) -> pd.Series:

        delta = self.df["close"].diff()

        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(
            alpha=1 / period,
            adjust=False,
        ).mean()

        avg_loss = loss.ewm(
            alpha=1 / period,
            adjust=False,
        ).mean()

        rs = avg_gain / avg_loss.replace(
            0,
            np.nan,
        )

        rsi = 100 - (
            100 / (1 + rs)
        )

        return rsi

    # --------------------------------------------------
    # MACD
    # --------------------------------------------------

    def macd(
        self,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> pd.DataFrame:

        fast_ema = self.df["close"].ewm(
            span=fast,
            adjust=False,
        ).mean()

        slow_ema = self.df["close"].ewm(
            span=slow,
            adjust=False,
        ).mean()

        macd_line = (
            fast_ema - slow_ema
        )

        signal_line = macd_line.ewm(
            span=signal,
            adjust=False,
        ).mean()

        histogram = (
            macd_line - signal_line
        )

        return pd.DataFrame(
            {
                "macd": macd_line,
                "signal": signal_line,
                "histogram": histogram,
            },
            index=self.df.index,
        )

    # --------------------------------------------------
    # ATR
    # --------------------------------------------------

    def atr(
        self,
        period: int = 14,
    ) -> pd.Series:

        previous_close = (
            self.df["close"].shift(1)
        )

        true_range = pd.concat(
            [
                self.df["high"]
                - self.df["low"],

                (
                    self.df["high"]
                    - previous_close
                ).abs(),

                (
                    self.df["low"]
                    - previous_close
                ).abs(),
            ],
            axis=1,
        ).max(axis=1)

        return true_range.ewm(
            alpha=1 / period,
            adjust=False,
        ).mean()

    # --------------------------------------------------
    # Bollinger Bands
    # --------------------------------------------------

    def bollinger_bands(
        self,
        period: int = 20,
        std_multiplier: float = 2.0,
    ) -> pd.DataFrame:

        middle = (
            self.df["close"]
            .rolling(period)
            .mean()
        )

        std = (
            self.df["close"]
            .rolling(period)
            .std()
        )

        upper = (
            middle
            + std_multiplier * std
        )

        lower = (
            middle
            - std_multiplier * std
        )

        return pd.DataFrame(
            {
                "upper": upper,
                "middle": middle,
                "lower": lower,
            },
            index=self.df.index,
        )

    # --------------------------------------------------
    # Stochastic
    # --------------------------------------------------

    def stochastic(
        self,
        period: int = 14,
        smooth_k: int = 3,
        smooth_d: int = 3,
    ) -> pd.DataFrame:

        lowest_low = (
            self.df["low"]
            .rolling(period)
            .min()
        )

        highest_high = (
            self.df["high"]
            .rolling(period)
            .max()
        )

        denominator = (
            highest_high - lowest_low
        )

        raw_k = (
            100
            * (
                self.df["close"]
                - lowest_low
            )
            / denominator.replace(
                0,
                np.nan,
            )
        )

        k = raw_k.rolling(
            smooth_k
        ).mean()

        d = k.rolling(
            smooth_d
        ).mean()

        return pd.DataFrame(
            {
                "k": k,
                "d": d,
            },
            index=self.df.index,
        )

    # --------------------------------------------------
    # ADX
    # --------------------------------------------------

    def adx(
        self,
        period: int = 14,
    ) -> pd.DataFrame:

        high = self.df["high"]
        low = self.df["low"]
        close = self.df["close"]

        up_move = high.diff()
        down_move = -low.diff()

        plus_dm = pd.Series(
            np.where(
                (up_move > down_move)
                & (up_move > 0),
                up_move,
                0.0,
            ),
            index=self.df.index,
        )

        minus_dm = pd.Series(
            np.where(
                (down_move > up_move)
                & (down_move > 0),
                down_move,
                0.0,
            ),
            index=self.df.index,
        )

        previous_close = close.shift(1)

        tr = pd.concat(
            [
                high - low,
                (high - previous_close).abs(),
                (low - previous_close).abs(),
            ],
            axis=1,
        ).max(axis=1)

        atr = tr.ewm(
            alpha=1 / period,
            adjust=False,
        ).mean()

        plus_di = (
            100
            * plus_dm.ewm(
                alpha=1 / period,
                adjust=False,
            ).mean()
            / atr.replace(0, np.nan)
        )

        minus_di = (
            100
            * minus_dm.ewm(
                alpha=1 / period,
                adjust=False,
            ).mean()
            / atr.replace(0, np.nan)
        )

        dx = (
            100
            * (
                plus_di - minus_di
            ).abs()
            / (
                plus_di + minus_di
            ).replace(0, np.nan)
        )

        adx = dx.ewm(
            alpha=1 / period,
            adjust=False,
        ).mean()

        return pd.DataFrame(
            {
                "adx": adx,
                "plus_di": plus_di,
                "minus_di": minus_di,
            },
            index=self.df.index,
        )

    # --------------------------------------------------
    # Add common indicators
    # --------------------------------------------------

    def calculate_all(
        self,
    ) -> pd.DataFrame:

        result = self.df.copy()

        result["sma_20"] = self.sma(20)
        result["sma_50"] = self.sma(50)
        result["sma_200"] = self.sma(200)

        result["ema_9"] = self.ema(9)
        result["ema_20"] = self.ema(20)
        result["ema_50"] = self.ema(50)
        result["ema_200"] = self.ema(200)

        result["rsi_14"] = self.rsi(14)

        macd = self.macd()

        result["macd"] = macd["macd"]
        result["macd_signal"] = macd["signal"]
        result["macd_histogram"] = (
            macd["histogram"]
        )

        result["atr_14"] = self.atr(14)

        bb = self.bollinger_bands()

        result["bb_upper"] = bb["upper"]
        result["bb_middle"] = bb["middle"]
        result["bb_lower"] = bb["lower"]

        stochastic = self.stochastic()

        result["stoch_k"] = stochastic["k"]
        result["stoch_d"] = stochastic["d"]

        adx = self.adx()

        result["adx"] = adx["adx"]
        result["plus_di"] = adx["plus_di"]
        result["minus_di"] = adx["minus_di"]

        return result
