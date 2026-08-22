import asyncio

from core.application import Application, create_app


class RecordingServices:
    def __init__(self):
        self.events: list[str] = []

    async def start_all(self) -> None:
        self.events.append("start_all")

    async def stop_all(self) -> None:
        self.events.append("stop_all")

    def health(self) -> dict[str, str]:
        self.events.append("health")
        return {"status": "ok"}


def test_application_start_delegates_to_service_manager():
    app = Application()
    services = RecordingServices()
    app.services = services

    asyncio.run(app.start())

    assert services.events == ["start_all"]


def test_application_stop_delegates_to_service_manager():
    app = Application()
    services = RecordingServices()
    app.services = services

    asyncio.run(app.stop())

    assert services.events == ["stop_all"]


def test_application_health_combines_application_and_service_health(monkeypatch):
    app = Application()
    services = RecordingServices()
    app.services = services
    monkeypatch.setattr("core.application.health_check", lambda: {"status": "ok"})

    result = app.health()

    assert result == {
        "application": {"status": "ok"},
        "services": {"status": "ok"},
    }
    assert services.events == ["health"]


def test_create_app_registers_telegram_service():
    app = create_app()

    assert "telegram" in app.services.services
