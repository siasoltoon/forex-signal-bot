from __future__ import annotations

import logging

from core.logger import setup_logger


# Compatibility layer for legacy imports.
def get_logger(name: str) -> logging.Logger:
    logger = setup_logger()
    return logging.LoggerAdapter(logger, {"component": name}).logger
