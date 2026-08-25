from __future__ import annotations

from typing import Any


class ApplicationError(Exception):
    """Base application exception with structured metadata."""

    code = "application_error"

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(ApplicationError):
    """Configuration related errors."""

    code = "configuration_error"


class ServiceInitializationError(ApplicationError):
    """Service startup errors."""

    code = "service_initialization_error"


class TemporaryServiceError(ApplicationError):
    """Recoverable temporary service failures."""

    code = "temporary_service_error"


class ProviderConnectionError(TemporaryServiceError):
    """External market provider connection failures."""

    code = "provider_connection_error"


class DataValidationError(ApplicationError):
    """Invalid or corrupted market data errors."""

    code = "data_validation_error"


__all__ = [
    "ApplicationError",
    "ConfigurationError",
    "ServiceInitializationError",
    "TemporaryServiceError",
    "ProviderConnectionError",
    "DataValidationError",
]
