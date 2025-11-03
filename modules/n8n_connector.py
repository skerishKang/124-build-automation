import os, json
import urllib.request

def post_to_n8n(payload: dict):
    base = os.getenv("N8N_BASE_URL")
    path = os.getenv("N8N_WEBHOOK_PATH","/webhook")
    if not base:
        return {"ok": False, "reason":"N8N_BASE_URL empty"}
    url = base.rstrip("/") + path
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=15) as res:
        body = res.read().decode("utf-8","replace")
        return {"ok": True, "status": res.status, "body": body}
