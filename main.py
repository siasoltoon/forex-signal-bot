import asyncio

from app import create_app


async def main() -> None:

    app = create_app()

    await app.start()


if __name__ == "__main__":

    asyncio.run(main())
