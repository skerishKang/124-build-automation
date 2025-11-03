import os
from contextlib import contextmanager

class AlreadyRunning(Exception):
    pass

@contextmanager
def file_lock(lock_name: str = "automation_hub.lock"):
    lock_path = os.path.abspath(lock_name)
    if os.path.exists(lock_path):
        raise AlreadyRunning(f"Lock exists: {lock_path}")
    with open(lock_path, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))
    try:
        yield
    finally:
        try:
            if os.path.exists(lock_path):
                os.remove(lock_path)
        except Exception:
            pass
