from __future__ import annotations

from typing import Any

from core.logger import setup_logger


logger = setup_logger()



class ApplicationError(Exception):
    """
    Base application exception.
    """


    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:

        super().__init__(
            message
        )

        self.message = message

        self.details = details or {}



def handle_exception(
    error: Exception,
) -> None:
    """
    Central exception handler.
    """


    logger.exception(
        "Application error: %s",
        error,
    )
