from __future__ import annotations

from typing import Any

from core.logger import setup_logger


logger = setup_logger()


class ApplicationError(Exception):
    """Base exception for expected application-level failures."""

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
    code = "configuration_error"


class ServiceError(ApplicationError):
    code = "service_error"


class CriticalServiceError(ServiceError):
    code = "critical_service_error"


class DataError(ApplicationError):
    code = "data_error"


class ProviderError(DataError):
    code = "provider_error"


class RateLimitError(ProviderError):
    code = "rate_limit_error"


class ProviderTimeoutError(ProviderError):
    code = "provider_timeout"


class ProviderUnavailableError(ProviderError):
    code = "provider_unavailable"


class AnalysisError(ApplicationError):
    code = "analysis_error"


class AIError(ApplicationError):
    code = "ai_error"


class SignalError(ApplicationError):
    code = "signal_error"


class RiskError(ApplicationError):
    code = "risk_error"


def handle_exception(error: Exception, *, level: str = "exception") -> None:
    """Log an exception at a controlled boundary without swallowing context."""
    log_method = getattr(logger, level, logger.exception)
    log_method("%s: %s", getattr(error, "code", error.__class__.__name__), error)


__all__ = [
    "ApplicationError",
    "ConfigurationError",
    "ServiceError",
    "CriticalServiceError",
    "DataError",
    "ProviderError",
    "RateLimitError",
    "ProviderTimeoutError",
    "ProviderUnavailableError",
    "AnalysisError",
    "AIError",
    "SignalError",
    "RiskError",
    "handle_exception",
]
