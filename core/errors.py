from __future__ import annotations

from core.exceptions import ApplicationError
from core.logger import setup_logger


logger = setup_logger()


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
