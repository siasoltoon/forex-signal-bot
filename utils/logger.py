from __future__ import annotations

import logging

from core.logger import setup_logger


# Compatibility layer for legacy imports. Reuses the canonical handlers/configuration
# while preserving the legacy logger-name API.
def get_logger(name: str) -> logging.Logger:
    canonical = setup_logger()
    logger = logging.getLogger(name)
    logger.setLevel(canonical.level)
    logger.handlers.clear()

    for handler in canonical.handlers:
        logger.addHandler(handler)

    logger.propagate = False
    return logger
