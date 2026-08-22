from __future__ import annotations

from abc import ABC, abstractmethod


class BaseService(ABC):
    """Base class for all application services."""

    name: str = "base-service"
    critical: bool = False

    @abstractmethod
    def start(self) -> None:
        """Start service."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop service."""
        pass

    def health(self) -> dict[str, str]:
        """Return service health information."""
        return {
            "service": self.name,
            "status": "ok",
        }
