from __future__ import annotations

import asyncio

from app import create_app

from core.shutdown import ShutdownManager

from core.logger import setup_logger


logger = setup_logger()



async def main() -> None:

    app = create_app()

    shutdown = ShutdownManager()

    shutdown.setup()


    await app.start()


    logger.info(
        "Application running."
    )


    await shutdown.wait()


    logger.info(
        "Stopping application..."
    )


    await app.stop()



if __name__ == "__main__":

    asyncio.run(
        main()
    )
