# Supabase-backed conversation memory context manager
import os
from typing import List, Dict, Any
from datetime import datetime

try:
    from supabase import create_client
except Exception:
    create_client = None

from modules.gemini_client import generate_text_safe

class SupabaseStorage:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        # Prefer service role on server; fallback to anon for dev
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if not (self.url and self.key and create_client):
            self.client = None
        else:
            self.client = create_client(self.url, self.key)
        self.table = os.getenv("CONTEXT_TABLE", "conversations")

    def available(self) -> bool:
        return self.client is not None

    def add_message(self, chat_id: str, user_id: str, role: str, content: str, msg_type: str = "text", meta: Dict[str, Any] = None):
        if not self.available():
            return None
        data = {
            "chat_id": str(chat_id),
            "user_id": str(user_id) if user_id else None,
            "role": role,
            "content": content or "",
            "message_type": msg_type,
            "meta": meta or {},
        }
        return self.client.table(self.table).insert(data).execute()

    def get_recent(self, chat_id: str, limit: int = 12) -> List[Dict[str, Any]]:
        if not self.available():
            return []
        res = self.client.table(self.table) \
            .select("*") \
            .eq("chat_id", str(chat_id)) \
            .order("created_at", desc=True) \
            .limit(limit).execute()
        data = res.data or []
        data.reverse()  # oldest -> newest
        return data

    def clear(self, chat_id: str):
        if not self.available():
            return None
        return self.client.table(self.table).delete().eq("chat_id", str(chat_id)).execute()


class ContextManager:
    def __init__(self):
        self.enabled = os.getenv("CONTEXT_ENABLED", "true").lower() in ("1","true","yes","y")
        self.max_messages = int(os.getenv("CONTEXT_MAX_MESSAGES", "12"))
        self.compress_threshold = int(os.getenv("CONTEXT_COMPRESS_THRESHOLD", "12000"))
        self.storage = SupabaseStorage()

    def is_on(self) -> bool:
        return self.enabled and self.storage.available()

    def add(self, chat_id, user_id, role, content, msg_type="text", meta=None):
        if not self.is_on():
            return
        try:
            self.storage.add_message(chat_id, user_id, role, content, msg_type, meta)
        except Exception:
            pass

    def get_context(self, chat_id) -> List[Dict[str, str]]:
        if not self.is_on():
            return []
        try:
            msgs = self.storage.get_recent(chat_id, limit=self.max_messages)
            return [{"role": m.get("role","user"), "content": m.get("content","")} for m in msgs]
        except Exception:
            return []

    def compress_if_needed(self, chat_id):
        if not self.is_on():
            return
        msgs = self.storage.get_recent(chat_id, limit=self.max_messages)
        total_len = sum(len((m.get("content") or "")) for m in msgs)
        if total_len < self.compress_threshold:
            return
        head = msgs[:-5]
        if not head:
            return
        head_text = "\n\n".join(f"{m.get('role')}: {m.get('content')}" for m in head)
        res = generate_text_safe(
            f"다음 대화들을 500자 이내로 요약해 주세요:\n\n{head_text}",
            temperature=0.2, max_tokens=600
        )
        summary = res.get("text") if res.get("ok") else "[이전 대화 요약 실패]"
        # store as system message
        self.add(chat_id, None, "system", f"[이전 대화 요약]\n{summary}")


def build_prompt_with_context(ctx_mgr: ContextManager, chat_id: str, user_text: str) -> str:
    history = ctx_mgr.get_context(chat_id)
    context_block = "\n".join([f"{m['role']}: {m['content']}" for m in history])
    return (
        "아래는 사용자와 어시스턴트의 이전 대화입니다. 맥락을 반영해 응답하세요.\n\n"
        f"{context_block}\n\n"
        f"user: {user_text}\n\n"
        "assistant:"
    )
