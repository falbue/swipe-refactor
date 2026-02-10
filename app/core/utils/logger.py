import logging
import os
import sys


def setup(
    name: str,
    log_path: str,
    DEBUG: bool = False,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.handlers.clear()

    log_level = logging.DEBUG if DEBUG else logging.INFO
    logger.setLevel(log_level)

    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )

    if DEBUG is False:
        os.makedirs(log_path, exist_ok=True)
        log_file = os.path.join(log_path, "application.log")

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if DEBUG is True:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        logger.debug("Режим отладки активирован. Логи выводятся в консоль")

    return logger
