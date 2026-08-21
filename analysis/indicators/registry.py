from __future__ import annotations

from analysis.indicators.base import Indicator
from core.errors import ApplicationError
from core.logger import setup_logger


logger = setup_logger()


class IndicatorRegistry:
    """
    Registry for managing indicators.

    Responsibilities:
    - Register indicators.
    - Retrieve indicators by name.
    - Prevent duplicate registrations.
    """


    def __init__(self) -> None:
        self._indicators: dict[str, Indicator] = {}


    def register(
        self,
        indicator: Indicator,
    ) -> None:

        name = indicator.name.strip().lower()

        if not name:
            raise ApplicationError(
                "Indicator name cannot be empty."
            )

        if name in self._indicators:
            raise ApplicationError(
                f"Indicator already registered: {name}"
            )

        self._indicators[name] = indicator

        logger.info(
            "Indicator registered: %s",
            name,
        )


    def get(
        self,
        name: str,
    ) -> Indicator:

        normalized = name.strip().lower()

        indicator = self._indicators.get(
            normalized
        )

        if indicator is None:
            raise ApplicationError(
                f"Indicator not found: {name}"
            )

        return indicator


    def list_indicators(
        self,
    ) -> list[str]:

        return list(
            self._indicators.keys()
        )


indicator_registry = IndicatorRegistry()
