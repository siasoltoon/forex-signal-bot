from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class MarketContext:
    index: Any
    trend: str
    strength: float
    volatility: float
    location: str


@dataclass(frozen=True)
class LanceSetup:
    index: Any
    setup: str
    direction: str
    score: float
    context: str
    details: dict[str, Any]


class LanceBeggsAnalyzer:
    """
    Initial Lance Beggs inspired price-action engine.

    Focuses on:
    - Market context
    - Trend direction
    - Trend strength
    - Pullbacks
    - Momentum
    - Strength / weakness
    - Setup identification
    - Basic entry context

    This is a probabilistic analysis engine and does not
    generate standalone trading signals.
    """

    def __init__(
        self,
        trend_period: int = 20,
        momentum_period: int = 5,
        pullback_lookback: int = 5,
    ) -> None:

        if trend_period < 5:
            raise ValueError(
                "trend_period must be >= 5."
            )

        if momentum_period < 2:
            raise ValueError(
                "momentum_period must be >= 2."
            )

        if pullback_lookback < 2:
            raise ValueError(
                "pullback_lookback must be >= 2."
            )

        self.trend_period = trend_period
        self.momentum_period = momentum_period
        self.pullback_lookback = (
            pullback_lookback
        )

    @staticmethod
    def _validate(
        dataframe: pd.DataFrame,
    ) -> None:

        required = [
            "open",
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

    def _atr(
        self,
        dataframe: pd.DataFrame,
        period: int = 14,
    ) -> pd.Series:

        high = dataframe["high"]
        low = dataframe["low"]
        close = dataframe["close"]

        previous_close = close.shift(1)

        true_range = pd.concat(
            [
                high - low,
                (high - previous_close).abs(),
                (low - previous_close).abs(),
            ],
            axis=1,
        ).max(axis=1)

        return true_range.rolling(
            period
        ).mean()

    def _trend_strength(
        self,
        dataframe: pd.DataFrame,
        index: int,
    ) -> tuple[str, float]:

        if index < self.trend_period:
            return "neutral", 0.0

        closes = dataframe["close"].iloc[
            index - self.trend_period:
            index + 1
        ]

        first = float(closes.iloc[0])
        last = float(closes.iloc[-1])

        if first == 0:
            return "neutral", 0.0

        change = (
            last - first
        ) / abs(first)

        normalized = min(
            1.0,
            abs(change) * 100.0,
        )

        if change > 0:
            return "bullish", normalized

        if change < 0:
            return "bearish", normalized

        return "neutral", 0.0

    def detect_context(
        self,
        dataframe: pd.DataFrame,
    ) -> list[MarketContext]:

        self._validate(dataframe)

        atr = self._atr(
            dataframe
        )

        contexts: list[
            MarketContext
        ] = []

        for i in range(
            len(dataframe)
        ):

            trend, strength = (
                self._trend_strength(
                    dataframe,
                    i,
                )
            )

            current_atr = atr.iloc[i]

            if pd.isna(current_atr):
                volatility = 0.0
            else:
                volatility = float(
                    current_atr
                )

            close = float(
                dataframe["close"].iloc[i]
            )

            if i < self.trend_period:
                location = "unknown"

            else:
                window = dataframe.iloc[
                    i - self.trend_period:
                    i + 1
                ]

                highest = float(
                    window["high"].max()
                )

                lowest = float(
                    window["low"].min()
                )

                range_size = (
                    highest - lowest
                )

                if range_size <= 0:
                    location = "middle"

                else:
                    position = (
                        close - lowest
                    ) / range_size

                    if position >= 0.70:
                        location = "upper_range"

                    elif position <= 0.30:
                        location = "lower_range"

                    else:
                        location = "middle"

            contexts.append(
                MarketContext(
                    index=dataframe.index[i],
                    trend=trend,
                    strength=strength,
                    volatility=volatility,
                    location=location,
                )
            )

        return contexts

    def detect_momentum(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.Series:

        self._validate(dataframe)

        return (
            dataframe["close"]
            .pct_change(
                self.momentum_period
            )
        )

    def detect_pullbacks(
        self,
        dataframe: pd.DataFrame,
    ) -> list[LanceSetup]:

        self._validate(dataframe)

        contexts = self.detect_context(
            dataframe
        )

        momentum = (
            self.detect_momentum(
                dataframe
            )
        )

        setups: list[LanceSetup] = []

        for i in range(
            self.pullback_lookback,
            len(dataframe),
        ):

            context = contexts[i]

            if context.trend == "neutral":
                continue

            current = dataframe.iloc[i]
            previous = dataframe.iloc[i - 1]

            current_close = float(
                current["close"]
            )

            previous_close = float(
                previous["close"]
            )

            current_momentum = momentum.iloc[
                i
            ]

            if pd.isna(
                current_momentum
            ):
                continue

            # Bullish trend pullback.
            if context.trend == "bullish":

                pullback = (
                    current_close
                    < previous_close
                )

                recovery = (
                    current_close
                    > float(current["open"])
                )

                if pullback and recovery:

                    score = (
                        50.0
                        + context.strength
                        * 30.0
                    )

                    if (
                        current_momentum
                        > 0
                    ):
                        score += 10.0

                    setups.append(
                        LanceSetup(
                            index=dataframe.index[i],
                            setup="bullish_pullback",
                            direction="bullish",
                            score=min(
                                score,
                                100.0,
                            ),
                            context="bullish_trend",
                            details={
                                "momentum":
                                    float(
                                        current_momentum
                                    ),
                                "trend_strength":
                                    context.strength,
                            },
                        )
                    )

            # Bearish trend pullback.
            elif context.trend == "bearish":

                pullback = (
                    current_close
                    > previous_close
                )

                rejection = (
                    current_close
                    < float(current["open"])
                )

                if pullback and rejection:

                    score = (
                        50.0
                        + context.strength
                        * 30.0
                    )

                    if (
                        current_momentum
                        < 0
                    ):
                        score += 10.0

                    setups.append(
                        LanceSetup(
                            index=dataframe.index[i],
                            setup="bearish_pullback",
                            direction="bearish",
                            score=min(
                                score,
                                100.0,
                            ),
                            context="bearish_trend",
                            details={
                                "momentum":
                                    float(
                                        current_momentum
                                    ),
                                "trend_strength":
                                    context.strength,
                            },
                        )
                    )

        return setups

    def detect_strength_weakness(
        self,
        dataframe: pd.DataFrame,
    ) -> list[LanceSetup]:

        self._validate(dataframe)

        atr = self._atr(
            dataframe
        )

        results: list[
            LanceSetup
        ] = []

        for i in range(
            1,
            len(dataframe),
        ):

            current = dataframe.iloc[i]
            previous = dataframe.iloc[i - 1]

            current_range = (
                float(current["high"])
                - float(current["low"])
            )

            current_body = abs(
                float(current["close"])
                - float(current["open"])
            )

            average_range = atr.iloc[i]

            if pd.isna(
                average_range
            ):
                continue

            if (
                current_range
                > average_range * 1.5
                and current_body
                > current_range * 0.60
            ):

                direction = (
                    "bullish"
                    if float(
                        current["close"]
                    )
                    > float(current["open"])
                    else "bearish"
                )

                results.append(
                    LanceSetup(
                        index=dataframe.index[i],
                        setup="price_strength",
                        direction=direction,
                        score=80.0,
                        context="strong_momentum",
                        details={
                            "range":
                                current_range,
                            "atr":
                                float(
                                    average_range
                                ),
                        },
                    )
                )

            elif (
                current_range
                < average_range * 0.60
            ):

                previous_direction = (
                    "bullish"
                    if float(
                        previous["close"]
                    )
                    > float(previous["open"])
                    else "bearish"
                )

                results.append(
                    LanceSetup(
                        index=dataframe.index[i],
                        setup="price_weakness",
                        direction=(
                            "bearish"
                            if previous_direction
                            == "bullish"
                            else "bullish"
                        ),
                        score=60.0,
                        context="weak_follow_through",
                        details={
                            "range":
                                current_range,
                            "atr":
                                float(
                                    average_range
                                ),
                        },
                    )
                )

        return results

    def detect_breakout_context(
        self,
        dataframe: pd.DataFrame,
        lookback: int = 20,
    ) -> list[LanceSetup]:

        self._validate(dataframe)

        if lookback < 2:
            raise ValueError(
                "lookback must be >= 2."
            )

        results: list[
            LanceSetup
        ] = []

        for i in range(
            lookback,
            len(dataframe),
        ):

            current = dataframe.iloc[i]

            resistance = float(
                dataframe["high"]
                .iloc[
                    i - lookback:i
                ]
                .max()
            )

            support = float(
                dataframe["low"]
                .iloc[
                    i - lookback:i
                ]
                .min()
            )

            close = float(
                current["close"]
            )

            if close > resistance:

                results.append(
                    LanceSetup(
                        index=dataframe.index[i],
                        setup="breakout_long_context",
                        direction="bullish",
                        score=75.0,
                        context="range_breakout",
                        details={
                            "level":
                                resistance,
                            "close":
                                close,
                        },
                    )
                )

            elif close < support:

                results.append(
                    LanceSetup(
                        index=dataframe.index[i],
                        setup="breakout_short_context",
                        direction="bearish",
                        score=75.0,
                        context="range_breakout",
                        details={
                            "level":
                                support,
                            "close":
                                close,
                        },
                    )
                )

        return results

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        self._validate(dataframe)

        contexts = self.detect_context(
            dataframe
        )

        momentum = self.detect_momentum(
            dataframe
        )

        pullbacks = (
            self.detect_pullbacks(
                dataframe
            )
        )

        strength_weakness = (
            self.detect_strength_weakness(
                dataframe
            )
        )

        breakouts = (
            self.detect_breakout_context(
                dataframe
            )
        )

        setups = (
            pullbacks
            + strength_weakness
            + breakouts
        )

        bullish_score = sum(
            setup.score
            for setup in setups
            if setup.direction
            == "bullish"
        )

        bearish_score = sum(
            setup.score
            for setup in setups
            if setup.direction
            == "bearish"
        )

        if bullish_score > bearish_score:
            bias = "bullish"

        elif bearish_score > bullish_score:
            bias = "bearish"

        else:
            bias = "neutral"

        current_context = (
            contexts[-1]
            if contexts
            else None
        )

        return {
            "bias": bias,
            "bullish_score": round(
                bullish_score,
                2,
            ),
            "bearish_score": round(
                bearish_score,
                2,
            ),
            "current_context":
                current_context,
            "contexts": contexts,
            "momentum": momentum,
            "pullbacks": pullbacks,
            "strength_weakness":
                strength_weakness,
            "breakouts": breakouts,
            "setups": setups,
        }
