import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    logger.info("Forex Signal Bot is starting...")


if __name__ == "__main__":
    main()
