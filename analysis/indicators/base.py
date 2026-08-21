
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from data.models import Candle


@dataclass(frozen=True)
class IndicatorResult:
    """
    Standard indicator output.
    """

    name: str

    value: float

    metadata: dict[str, object] | None = None


class Indicator(ABC):
    """
    Base class for all technical indicators.

    Every indicator must:
    - Receive candle data.
    - Calculate a result.
    - Return a standardized output.
    """

    name: str = "unknown"


    @abstractmethod
    def calculate(
        self,
        candles: list[Candle],
    ) -> IndicatorResult:
        """
        Calculate indicator value.
        """

        raise NotImplementedError
