from __future__ import annotations

from typing import Any


class ApplicationError(Exception):
    """
    Base application exception.
    """

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(ApplicationError):
    """
    Configuration related errors.
    """


class ServiceInitializationError(ApplicationError):
    """
    Service startup errors.
    """
