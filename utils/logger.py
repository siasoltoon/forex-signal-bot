from __future__ import annotations

import logging
import os
from pathlib import Path


LOG_DIR = Path("logs")

LOG_DIR.mkdir(
    exist_ok=True
)


def get_logger(
    name: str
) -> logging.Logger:
    """
    Create application logger.
    """

    logger = logging.getLogger(
        name
    )

    if logger.handlers:
        return logger


    level = os.getenv(
        "LOG_LEVEL",
        "INFO",
    )


    logger.setLevel(
        level
    )


    formatter = logging.Formatter(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    )


    console = logging.StreamHandler()

    console.setFormatter(
        formatter
    )


    file = logging.FileHandler(
        LOG_DIR / "app.log",
        encoding="utf-8",
    )

    file.setFormatter(
        formatter
    )


    logger.addHandler(
        console
    )

    logger.addHandler(
        file
    )


    return logger
