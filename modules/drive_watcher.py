import os, json, pathlib
from modules.logging_setup import setup_logger

LOGGER = setup_logger("drive")

def _processed_db_path():
    root = pathlib.Path(__file__).resolve().parents[1]
    return str(root / "processed_files.json")

def _load_processed():
    p = _processed_db_path()
    if not os.path.exists(p):
        return set()
    try:
        return set(json.loads(open(p,"r",encoding="utf-8").read()))
    except Exception:
        return set()

def _save_processed(s: set):
    p = _processed_db_path()
    with open(p,"w",encoding="utf-8") as f:
        f.write(json.dumps(list(s), ensure_ascii=False, indent=2))

def poll_drive_once(fetch_list_func, handle_file_func):
    """
    fetch_list_func() -> list[dict]: [{id, name, mimeType}, ...]
    handle_file_func(file_dict) -> None
    """
    if not os.getenv("DRIVE_FOLDER_ID"):
        LOGGER.info("DRIVE_FOLDER_ID empty. Skip drive polling.")
        return
    processed = _load_processed()
    files = fetch_list_func() or []
    for f in files:
        fid = f.get("id")
        if not fid or fid in processed:
            continue
        try:
            handle_file_func(f)
            processed.add(fid)
        except Exception as e:
            LOGGER.exception(f"handle_file failed: {f}: {e}")
    _save_processed(processed)
    LOGGER.info(f"Drive poll done. processed={len(processed)}")
