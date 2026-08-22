from __future__ import annotations

from services.base import BaseService

from core.errors import handle_exception
from core.logger import setup_logger


logger = setup_logger()


class ServiceManager:
    """
    Manage application services.
    """

    def __init__(self) -> None:
        self.services: dict[str, BaseService] = {}

    def register(self, service: BaseService) -> None:
        self.services[service.name] = service

    async def start_all(self) -> None:
        for service in self.services.values():
            try:
                await service.start()
                logger.info("%s service started.", service.name)
            except Exception as error:
                handle_exception(error)

    async def stop_all(self) -> None:
        for service in reversed(list(self.services.values())):
            try:
                await service.stop()
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
                result[name] = {"status": "error"}
        return result
