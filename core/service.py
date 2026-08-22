from __future__ import annotations

from services.base import BaseService

from core.errors import CriticalServiceError, handle_exception
from core.logger import setup_logger


logger = setup_logger()


class ServiceManager:
    """Register, start, stop and health-check application services."""

    def __init__(self) -> None:
        self.services: dict[str, BaseService] = {}

    def register(self, service: BaseService) -> None:
        if service.name in self.services:
            raise ValueError(f"Service already registered: {service.name}")
        self.services[service.name] = service

    async def start_all(self) -> None:
        started: list[BaseService] = []

        for service in self.services.values():
            try:
                result = service.start()
                if hasattr(result, "__await__"):
                    await result
                started.append(service)
                logger.info("%s service started.", service.name)
            except Exception as error:
                handle_exception(error)
                if service.critical:
                    await self._stop_services(started)
                    raise CriticalServiceError(
                        f"Critical service failed to start: {service.name}",
                        {"service": service.name},
                    ) from error
                logger.warning(
                    "%s service failed to start; continuing in degraded mode.",
                    service.name,
                )

    async def stop_all(self) -> None:
        await self._stop_services(list(self.services.values()))

    async def _stop_services(self, services: list[BaseService]) -> None:
        for service in reversed(services):
            try:
                result = service.stop()
                if hasattr(result, "__await__"):
                    await result
                logger.info("%s service stopped.", service.name)
            except Exception as error:
                handle_exception(error)

    def health(self) -> dict:
        result = {}
        for name, service in self.services.items():
            try:
                result[name] = service.health()
            except Exception as error:
                handle_exception(error)
                result[name] = {
                    "service": name,
                    "status": "error",
                    "critical": service.critical,
                }
        return result
