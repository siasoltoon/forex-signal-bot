import logging


def setup_logger() -> logging.Logger:
    """
    Configure application logger.
    """

    logger = logging.getLogger(
        "forex-signal-bot"
    )

    logger.setLevel(
        logging.INFO
    )

    if not logger.handlers:

        handler = logging.StreamHandler()

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )

        handler.setFormatter(
            formatter
        )

        logger.addHandler(
            handler
        )

    return logger
