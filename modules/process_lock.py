import os, time, json
from contextlib import contextmanager

class AlreadyRunning(Exception):
    pass

def _read_lock(lock_path: str):
    try:
        with open(lock_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 구버전 락 파일(int만 저장) 또는 비정상 데이터를 처리합니다.
            # 딕셔너리 형태가 아니면 유효하지 않은 것으로 간주합니다.
            if isinstance(data, dict):
                return data
            return None
    except (json.JSONDecodeError, UnicodeDecodeError):
        # 파일이 비어있거나 JSON 형식이 아닌 경우, 유효하지 않은 것으로 간주합니다.
        return None
    except Exception:
        return None

def _pid_alive(pid: int) -> bool:
    # psutil 있으면 정확, 없으면 best-effort
    try:
        import psutil  # type: ignore
        return psutil.pid_exists(pid)
    except Exception:
        # 윈도우 기본에선 정확 체크 어렵습니다. 보수적으로 True 반환.
        try:
            os.kill(pid, 0)  # 유닉스식, 윈도우에선 AccessDenied 가능
            return True
        except Exception:
            return False

@contextmanager
def file_lock(lock_name: str = "automation_hub.lock", stale_seconds: int = 6*60*60):
    """
    - 락 파일에 {"pid":..., "ts":...} 저장
    - 기존 락이 있으면:
      - PID 살아있으면 AlreadyRunning
      - PID 없고 락 오래되었거나 죽은 프로세스면 자동 제거 후 획득
    """
    lock_path = os.path.abspath(lock_name)

    if os.path.exists(lock_path):
        meta = _read_lock(lock_path) or {}
        pid = meta.get("pid")
        ts = float(meta.get("ts", 0.0))
        age = time.time() - ts if ts else 0.0

        if isinstance(pid, int) and _pid_alive(pid):
            # 실제로 다른 인스턴스가 돌고 있음
            raise AlreadyRunning(f"Lock exists: {lock_path}")
        else:
            # 고아 락이거나 너무 오래된 락: 제거
            if age > 1 or not pid:
                try:
                    os.remove(lock_path)
                except Exception:
                    pass

    # 새 락 생성
    with open(lock_path, "w", encoding="utf-8") as f:
        json.dump({"pid": os.getpid(), "ts": time.time()}, f)

    try:
        yield
    finally:
        try:
            if os.path.exists(lock_path):
                os.remove(lock_path)
        except Exception:
            pass