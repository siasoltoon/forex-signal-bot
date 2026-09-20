from __future__ import annotations

import asyncio
import signal

from core.logger import setup_logger
from config.settings import Settings
from .executors import register_real_executors
from .handlers import register_default_handlers
from .pull_client import WorkerPullClient, WorkerPullSettings
from .runtime import WorkerRuntime
from .server import WorkerHTTPServer

logger = setup_logger()
settings = Settings.load()


async def main_async() -> None:
    runtime = WorkerRuntime.create()
    register_default_handlers(runtime)
    register_real_executors(runtime)

    server = WorkerHTTPServer(runtime)
    server.start()
    logger.info(
        "PC Worker %s ready on %s:%s",
        runtime.worker_id,
        server.host,
        server.port,
    )

    stop_event = asyncio.Event()

    def shutdown(*_args: object) -> None:
        stop_event.set()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    pull_settings = WorkerPullSettings.from_env()
    pull_task: asyncio.Task[None] | None = None
    if pull_settings is not None:
        logger.info(
            "PC Worker pull transport enabled: %s (poll %.1fs)",
            pull_settings.base_url,
            pull_settings.poll_interval_seconds,
        )
        pull_task = asyncio.create_task(
            WorkerPullClient(pull_settings).run(runtime, stop_event)
        )

    try:
        await stop_event.wait()
    finally:
        if pull_task is not None:
            pull_task.cancel()
            await asyncio.gather(pull_task, return_exceptions=True)
        server.stop()


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
