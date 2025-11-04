import os, sys, logging
from logging import StreamHandler, Formatter
from modules.process_lock import file_lock, AlreadyRunning
from modules.logging_setup import setup_logger
from modules.env_check import assert_env

def _bootstrap_console_logger():
    logger = logging.getLogger("runner")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    sh = StreamHandler()
    sh.setFormatter(Formatter("[%(asctime)s] %(levelname)s - %(name)s - %(message)s"))
    logger.addHandler(sh)
    return logger

def run_polling():
    import main_enhanced as app
    if hasattr(app, "main"): app.main()
    else: raise RuntimeError("main_enhanced.py에 main() 함수가 필요합니다.")

def run_webhook():
    import main_webhook as app
    if hasattr(app, "main"): app.main()
    else: raise RuntimeError("main_webhook.py에 main() 함수가 필요합니다.")

def main():
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        # Load backend.env first (lower precedence), then .env/.env.local override
        for _p in ("backend.env", ".env", ".env.local"):
            try:
                if os.path.exists(_p):
                    load_dotenv(dotenv_path=_p, override=(_p != "backend.env"))
            except Exception:
                pass
    except ImportError:
        pass

    # 1) 우선 콘솔만 찍는 부트스트랩 로거 (파일 잠돌 충돌 회피)
    logger = _bootstrap_console_logger()
    assert_env()

    mode = (os.getenv("BOT_MODE","polling")).lower()
    lock_name = os.getenv("LOCK_FILE","automation_hub.lock")
    # Ensure log directory exists when using file-based logging
    try:
        log_file = os.getenv("LOG_FILE")
        if log_file:
            d = os.path.dirname(log_file)
            if d:
                os.makedirs(d, exist_ok=True)
    except Exception:
        pass

    try:
        # 2) 락 먼저 획득
        with file_lock(lock_name):
            # 3) 이제 파일 로거로 업그레이드 (로테이션 핸들러 포함)
            logger = setup_logger("runner")

            if mode == "webhook":
                logger.info("Starting in WEBHOOK mode")
                run_webhook()
            else:
                logger.info("Starting in POLLING mode")
                run_polling()

    except AlreadyRunning as e:
        # 여기도 콘솔 로거만 사용 (파일 핸들러 금지)
        logger = _bootstrap_console_logger()
        logger.error(f"{e}. Another instance is running. Exit.")
        sys.exit(1)

if __name__ == "__main__":
    main()
