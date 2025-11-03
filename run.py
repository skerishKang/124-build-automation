import os, sys
from modules.process_lock import file_lock, AlreadyRunning
from modules.logging_setup import setup_logger
from modules.env_check import assert_env

def run_polling():
    import main_enhanced as app
    if hasattr(app, "main"):
        app.main()
    else:
        raise RuntimeError("main_enhanced.py에 main() 함수가 필요합니다.")

def run_webhook():
    import main_webhook as app
    if hasattr(app, "main"):
        app.main()
    else:
        raise RuntimeError("main_webhook.py에 main() 함수가 필요합니다.")

def main():
    logger = setup_logger("runner")
    assert_env()
    mode = (os.getenv("BOT_MODE","polling")).lower()
    lock_name = os.getenv("LOCK_FILE","automation_hub.lock")
    try:
        with file_lock(lock_name):
            if mode == "webhook":
                logger.info("Starting in WEBHOOK mode")
                run_webhook()
            else:
                logger.info("Starting in POLLING mode")
                run_polling()
    except AlreadyRunning as e:
        logger.error(f"{e}. Another instance is running. Exit.")
        sys.exit(1)

if __name__ == "__main__":
    main()
