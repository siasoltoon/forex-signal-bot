import asyncio

from core.shutdown import ShutdownManager


def test_shutdown_manager_trigger_sets_event():
    manager = ShutdownManager()

    assert manager.event.is_set() is False

    manager.trigger()

    assert manager.event.is_set() is True


def test_shutdown_manager_wait_returns_after_trigger():
    async def scenario():
        manager = ShutdownManager()
        manager.trigger()
        await asyncio.wait_for(manager.wait(), timeout=0.1)
        assert manager.event.is_set() is True

    asyncio.run(scenario())
