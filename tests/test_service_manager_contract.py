import pytest

from core.service import ServiceManager
from services.base import BaseService


class RecordingService(BaseService):
    def __init__(self, name: str, events: list[str], *, fail_start=False, fail_stop=False, fail_health=False):
        self.name = name
        self.events = events
        self.fail_start = fail_start
        self.fail_stop = fail_stop
        self.fail_health = fail_health

    def start(self) -> None:
        self.events.append(f"start:{self.name}")
        if self.fail_start:
            raise RuntimeError(f"start failed: {self.name}")

    def stop(self) -> None:
        self.events.append(f"stop:{self.name}")
        if self.fail_stop:
            raise RuntimeError(f"stop failed: {self.name}")

    def health(self) -> dict[str, str]:
        self.events.append(f"health:{self.name}")
        if self.fail_health:
            raise RuntimeError(f"health failed: {self.name}")
        return {"service": self.name, "status": "ok"}


def test_register_uses_service_name_as_stable_key():
    manager = ServiceManager()
    events: list[str] = []
    service = RecordingService("alpha", events)

    manager.register(service)

    assert manager.services == {"alpha": service}


@pytest.mark.asyncio
async def test_start_all_preserves_registration_order_and_continues_after_error(monkeypatch):
    manager = ServiceManager()
    events: list[str] = []
    first = RecordingService("first", events)
    failing = RecordingService("failing", events, fail_start=True)
    last = RecordingService("last", events)
    for service in (first, failing, last):
        manager.register(service)

    handled: list[Exception] = []
    monkeypatch.setattr("core.service.handle_exception", handled.append)

    await manager.start_all()

    assert events == ["start:first", "start:failing", "start:last"]
    assert len(handled) == 1
    assert str(handled[0]) == "start failed: failing"


@pytest.mark.asyncio
async def test_stop_all_uses_reverse_registration_order_and_continues_after_error(monkeypatch):
    manager = ServiceManager()
    events: list[str] = []
    first = RecordingService("first", events)
    failing = RecordingService("failing", events, fail_stop=True)
    last = RecordingService("last", events)
    for service in (first, failing, last):
        manager.register(service)

    handled: list[Exception] = []
    monkeypatch.setattr("core.service.handle_exception", handled.append)

    await manager.stop_all()

    assert events == ["stop:last", "stop:failing", "stop:first"]
    assert len(handled) == 1
    assert str(handled[0]) == "stop failed: failing"


def test_health_returns_each_service_health():
    manager = ServiceManager()
    events: list[str] = []
    manager.register(RecordingService("alpha", events))
    manager.register(RecordingService("beta", events))

    result = manager.health()

    assert result == {
        "alpha": {"service": "alpha", "status": "ok"},
        "beta": {"service": "beta", "status": "ok"},
    }
    assert events == ["health:alpha", "health:beta"]


def test_health_converts_service_exception_to_structured_error_and_continues(monkeypatch):
    manager = ServiceManager()
    events: list[str] = []
    healthy = RecordingService("healthy", events)
    failing = RecordingService("failing", events, fail_health=True)
    manager.register(healthy)
    manager.register(failing)

    handled: list[Exception] = []
    monkeypatch.setattr("core.service.handle_exception", handled.append)

    result = manager.health()

    assert result == {
        "healthy": {"service": "healthy", "status": "ok"},
        "failing": {"status": "error"},
    }
    assert len(handled) == 1
    assert str(handled[0]) == "health failed: failing"
    assert events == ["health:healthy", "health:failing"]


@pytest.mark.asyncio
async def test_lifecycle_contract_supports_async_service_methods(monkeypatch):
    manager = ServiceManager()
    events: list[str] = []

    class AsyncService(BaseService):
        name = "async"

        async def start(self) -> None:
            events.append("start:async")

        async def stop(self) -> None:
            events.append("stop:async")

    manager.register(AsyncService())
    monkeypatch.setattr("core.service.handle_exception", lambda error: pytest.fail(str(error)))

    await manager.start_all()
    await manager.stop_all()

    assert events == ["start:async", "stop:async"]
