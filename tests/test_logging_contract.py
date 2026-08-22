import logging

from core.logger import setup_logger
from utils.logger import get_logger


def test_legacy_logger_uses_canonical_logger():
    canonical = setup_logger()
    legacy = get_logger("test")

    assert legacy is canonical
    assert legacy.name == "forex-signal-bot"


def test_canonical_logger_has_expected_handlers():
    logger = setup_logger()

    assert logger.name == "forex-signal-bot"
    assert any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers)
    assert any(isinstance(handler, logging.FileHandler) for handler in logger.handlers)
