import os
from modules.logging_setup import setup_logger
LOGGER = setup_logger("gmail")

def poll_gmail_once(list_threads_func, fetch_message_func, handle_message_func):
    if os.getenv("GMAIL_WATCH_ENABLE","false").lower() != "true":
        LOGGER.info("Gmail polling disabled.")
        return
    try:
        tids = list_threads_func() or []
        for tid in tids:
            msg = fetch_message_func(tid)
            if msg:
                handle_message_func(msg)
    except Exception as e:
        LOGGER.exception(f"Gmail poll error: {e}")
