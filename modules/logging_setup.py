import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name: str = "automation", log_file: str = None, level: str = None):
    log_level = getattr(logging, (level or os.getenv("LOG_LEVEL","INFO")).upper(), logging.INFO)
    log_file = log_file or os.getenv("LOG_FILE","automation_hub.log")
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.handlers.clear()

    formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(name)s - %(message)s")

    fh = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    return logger
