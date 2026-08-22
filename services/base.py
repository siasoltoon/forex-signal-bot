from __future__ import annotations

from abc import ABC, abstractmethod


class BaseService(ABC):
    """
    Base class for all application services.
    """

    name: str = "base-service"

    @abstractmethod
    async def start(self) -> None:
        """
        Start service.
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """
        Stop service.
        """
        pass

    def health(self) -> dict[str, str]:
        """
        Service health information.
        """
        return {
            "service": self.name,
            "status": "ok",
        }
