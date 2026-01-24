import logging
import time


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logging.info("Bot service stub running")
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
