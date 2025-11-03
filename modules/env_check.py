import os
from modules.logging_setup import setup_logger
REQ_KEYS = ["BOT_MODE","LOG_FILE"]

def assert_env():
    logger = setup_logger("env")
    missing = [k for k in REQ_KEYS if not os.getenv(k)]
    if missing:
        logger.warning(f"Missing env keys: {missing}")
