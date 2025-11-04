import os
from modules.logging_setup import setup_logger

def _required_keys() -> list:
    keys = ["BOT_MODE", "LOG_FILE", "TELEGRAM_TOKEN"]
    provider = (os.getenv("LLM_PROVIDER", "gemini") or "gemini").lower()
    if provider == "minimax":
        keys += ["MINIMAX_API_TOKEN", "MINIMAX_BASE_URL"]
    else:
        keys += ["GEMINI_API_KEY"]
    return keys

def assert_env():
    logger = setup_logger("env")
    req = _required_keys()
    missing = [k for k in req if not os.getenv(k)]
    if missing:
        logger.warning(f"Missing env keys: {missing}")
