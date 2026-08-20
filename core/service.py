from __future__ import annotations

from services.base import BaseService


class ServiceManager:
    """
    Manage application services.
    """


    def __init__(self) -> None:

        self.services: dict[str, BaseService] = {}


    def register(
        self,
        service: BaseService
    ) -> None:

        self.services[
            service.name
        ] = service


    def start_all(self) -> None:

        for service in self.services.values():

            service.start()


    def stop_all(self) -> None:

        for service in reversed(
            list(self.services.values())
        ):

            service.stop()


    def health(self) -> dict:

        return {
            name: service.health()
            for name, service in self.services.items()
        }
