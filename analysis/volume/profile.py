from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class VolumeNode:
    price: float
    volume: float
    percentage: float


@dataclass(frozen=True)
class VolumeProfileResult:
    poc: float
    value_area_high: float
    value_area_low: float
    total_volume: float
    hvn: list[VolumeNode]
    lvn: list[VolumeNode]


class VolumeProfileAnalyzer:
    """
    Volume Profile analysis engine.

    Calculates:
    - POC (Point of Control)
    - Value Area High
    - Value Area Low
    - HVN (High Volume Nodes)
    - LVN (Low Volume Nodes)

    Expected columns:
    open, high, low, close, volume
    """

    def __init__(
        self,
        bins: int = 50,
        value_area_percentage: float = 0.70,
    ) -> None:

        if bins < 5:
            raise ValueError(
                "bins must be >= 5."
            )

        if not 0 < value_area_percentage <= 1:
            raise ValueError(
                "value_area_percentage must be between 0 and 1."
            )

        self.bins = bins
        self.value_area_percentage = (
            value_area_percentage
        )

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

    def _build_profile(
        self,
        dataframe: pd.DataFrame,
    ) -> tuple[np.ndarray, np.ndarray]:

        lows = dataframe["low"].to_numpy(
            dtype=float
        )

        highs = dataframe["high"].to_numpy(
            dtype=float
        )

        closes = dataframe["close"].to_numpy(
            dtype=float
        )

        volumes = dataframe["volume"].to_numpy(
            dtype=float
        )

        minimum = float(
            np.nanmin(lows)
        )

        maximum = float(
            np.nanmax(highs)
        )

        if maximum <= minimum:
            maximum = minimum + 1e-9

        edges = np.linspace(
            minimum,
            maximum,
            self.bins + 1,
        )

        profile = np.zeros(
            self.bins,
            dtype=float,
        )

        for low, high, close, volume in zip(
            lows,
            highs,
            closes,
            volumes,
        ):

            if not np.isfinite(volume):
                continue

            if volume < 0:
                continue

            candle_low = min(
                low,
                high,
            )

            candle_high = max(
                low,
                high,
            )

            if candle_high <= candle_low:
                index = np.searchsorted(
                    edges,
                    close,
                    side="right",
                ) - 1

                index = max(
                    0,
                    min(
                        self.bins - 1,
                        index,
                    ),
                )

                profile[index] += volume
                continue

            candle_range = (
                candle_high
                - candle_low
            )

            start = max(
                0,
                np.searchsorted(
                    edges,
                    candle_low,
                    side="right",
                ) - 1,
            )

            end = min(
                self.bins - 1,
                np.searchsorted(
                    edges,
                    candle_high,
                    side="left",
                ),
            )

            touched_bins = (
                end - start + 1
            )

            if touched_bins <= 0:
                continue

            distributed_volume = (
                volume
                / touched_bins
            )

            for index in range(
                start,
                end + 1,
            ):
                profile[index] += (
                    distributed_volume
                )

        centers = (
            edges[:-1]
            + np.diff(edges) / 2
        )

        return centers, profile

    def calculate(
        self,
        dataframe: pd.DataFrame,
    ) -> VolumeProfileResult:

        self._validate(dataframe)

        prices, volumes = (
            self._build_profile(
                dataframe
            )
        )

        total_volume = float(
            volumes.sum()
        )

        if total_volume <= 0:
            raise ValueError(
                "Total volume must be greater than zero."
            )

        poc_index = int(
            np.argmax(volumes)
        )

        poc = float(
            prices[poc_index]
        )

        target_volume = (
            total_volume
            * self.value_area_percentage
        )

        included = {
            poc_index
        }

        current_volume = float(
            volumes[poc_index]
        )

        left = poc_index - 1
        right = poc_index + 1

        while (
            current_volume < target_volume
            and (
                left >= 0
                or right < len(volumes)
            )
        ):

            left_volume = (
                volumes[left]
                if left >= 0
                else -1
            )

            right_volume = (
                volumes[right]
                if right < len(volumes)
                else -1
            )

            if (
                right_volume
                >= left_volume
            ):

                if right >= len(volumes):
                    break

                included.add(right)

                current_volume += float(
                    volumes[right]
                )

                right += 1

            else:

                if left < 0:
                    break

                included.add(left)

                current_volume += float(
                    volumes[left]
                )

                left -= 1

        value_area_low = float(
            prices[min(included)]
        )

        value_area_high = float(
            prices[max(included)]
        )

        max_volume = float(
            volumes.max()
        )

        percentages = np.divide(
            volumes,
            total_volume,
            out=np.zeros_like(volumes),
            where=volumes != 0,
        )

        nodes = [
            VolumeNode(
                price=float(prices[i]),
                volume=float(volumes[i]),
                percentage=float(
                    percentages[i]
                ),
            )
            for i in range(
                len(prices)
            )
            if volumes[i] > 0
        ]

        if max_volume > 0:

            hvn_threshold = (
                max_volume * 0.70
            )

            lvn_threshold = (
                max_volume * 0.20
            )

        else:

            hvn_threshold = 0
            lvn_threshold = 0

        hvn = [
            node
            for node in nodes
            if node.volume
            >= hvn_threshold
        ]

        lvn = [
            node
            for node in nodes
            if node.volume
            <= lvn_threshold
        ]

        return VolumeProfileResult(
            poc=poc,
            value_area_high=value_area_high,
            value_area_low=value_area_low,
            total_volume=total_volume,
            hvn=hvn,
            lvn=lvn,
        )

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        result = self.calculate(
            dataframe
        )

        return {
            "poc": result.poc,
            "value_area_high":
                result.value_area_high,
            "value_area_low":
                result.value_area_low,
            "total_volume":
                result.total_volume,
            "hvn": result.hvn,
            "lvn": result.lvn,
        }
