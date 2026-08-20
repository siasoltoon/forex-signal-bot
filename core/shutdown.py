from __future__ import annotations

import asyncio
import signal

from core.logger import setup_logger


logger = setup_logger()



class ShutdownManager:
    """
    Handle application shutdown signals.
    """


    def __init__(self) -> None:

        self.event = asyncio.Event()


    def setup(self) -> None:
        """
        Register system signals.
        """

        loop = asyncio.get_running_loop()


        for sig in (
            signal.SIGINT,
            signal.SIGTERM,
        ):

            loop.add_signal_handler(
                sig,
                self.trigger,
            )


    def trigger(self) -> None:
        """
        Trigger shutdown.
        """

        logger.warning(
            "Shutdown signal received."
        )

        self.event.set()


    async def wait(self) -> None:
        """
        Wait for shutdown.
        """

        await self.event.wait()
