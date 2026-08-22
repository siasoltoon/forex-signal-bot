import logging

from core.logger import setup_logger
from utils.logger import get_logger


def test_legacy_logger_preserves_name_and_reuses_canonical_handlers():
    canonical = setup_logger()
    legacy = get_logger("test")

    assert legacy.name == "test"
    assert legacy.level == canonical.level
    assert legacy.handlers == canonical.handlers
    assert legacy.propagate is False


def test_canonical_logger_has_expected_handlers():
    logger = setup_logger()

    assert logger.name == "forex-signal-bot"
    assert any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers)
    assert any(isinstance(handler, logging.FileHandler) for handler in logger.handlers)
