import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def logger_setup():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s - '
        '%(filename)s - %(funcName)s - %(lineno)d'
    )
    os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)
    handler = RotatingFileHandler(
        f'{BASE_DIR}/logs/logger.log', maxBytes=2_560_000, backupCount=5
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
