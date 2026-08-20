import logging
import sys


def setup_logger(level: str = "INFO") -> logging.Logger:
    """
    Configure the application-wide logger.
    """

    logger = logging.getLogger()

    if logger.handlers:
        return logger

    logger.setLevel(
        getattr(
            logging,
            level.upper(),
            logging.INFO,
        )
    )

    handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger
