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

    def get_total_chars(self, chat_id: str) -> int:
        if not self.available():
            return 0
        res = self.client.table(self.table) \
            .select("content") \
            .eq("chat_id", str(chat_id)) \
            .execute()
        if not res.data:
            return 0
        return sum(len(msg.get("content", "")) for msg in res.data)

class ContextManager:
    def __init__(self):
        self.storage = SupabaseStorage()
        self.enabled = os.getenv("CONTEXT_ENABLED", "true").lower() == "true"
        if self.enabled and not self.storage.available():
            self.enabled = False

    def available(self) -> bool:
        return self.enabled and self.storage.available()

    def add(self, chat_id: str, user_id: str, role: str, content: str, msg_type: str = "text", meta: Dict[str, Any] = None):
        if not self.available():
            return
        try:
            self.storage.add_message(chat_id, user_id, role, content, msg_type, meta)
        except Exception as e:
            print(f"Failed to add message: {e}")

    def get_context(self, chat_id: str, limit: int = None) -> List[Dict[str, Any]]:
        if not self.available():
            return []
        limit = limit or int(os.getenv("CONTEXT_MAX_MESSAGES", "12"))
        return self.storage.get_recent(chat_id, limit)

    def compress_if_needed(self, chat_id: str):
        if not self.available():
            return
        try:
            threshold = int(os.getenv("CONTEXT_COMPRESS_THRESHOLD", "12000"))
            max_msgs = int(os.getenv("CONTEXT_MAX_MESSAGES", "12"))
            current_chars = self.storage.get_total_chars(chat_id)
            if current_chars > threshold:
                # Compress conversation
                recent_msgs = self.storage.get_recent(chat_id, max_msgs)
                if not recent_msgs:
                    return
                conversation_text = "\n".join([
                    f"{msg['role']}: {msg['content']}"
                    for msg in recent_msgs
                ])
                prompt = f" compress this conversation to key points (max 300 words):\n\n{conversation_text}"
                compress_res = generate_text_safe(prompt, temperature=0.3, max_tokens=500)
                if compress_res.get("ok") and compress_res.get("text"):
                    summary = compress_res["text"]
                    # Delete old messages
                    self.client = self.storage.client
                    self.client.table(self.storage.table) \
                        .delete() \
                        .eq("chat_id", str(chat_id)) \
                        .execute()
                    # Add summary as system message
                    self.storage.add_message(
                        chat_id, None, "system", f"[이전 대화 요약]\n{summary}", "system"
                    )
        except Exception as e:
            print(f"Compression failed: {e}")

def build_prompt_with_context(ctx_mgr: ContextManager, chat_id: str, current_text: str) -> str:
    if not ctx_mgr.available():
        return f"사용자의 요청: {current_text}\n\n이 요청에 대해 자연스럽게 대화하거나, 필요한 경우 분석/요약하여 응답해주세요."
    try:
        context_msgs = ctx_mgr.get_context(chat_id, limit=8)
        if not context_msgs:
            return f"사용자의 요청: {current_text}\n\n이 요청에 대해 자연스럽게 대화하거나, 필요한 경우 분석/요약하여 응답해주세요."
        context_parts = []
        for msg in context_msgs:
            role = "사용자" if msg.get("role") == "user" else "어시스턴트"
            content = msg.get("content", "")
            if msg.get("message_type") == "voice":
                content = f"[음성 전사] {content}"
            elif msg.get("message_type") == "image":
                content = f"[이미지 분석] {content}"
            context_parts.append(f"{role}: {content}")
        context_text = "\n".join(context_parts)
        return f"""최근 대화 맥락:
{context_text}

사용자의 현재 요청: {current_text}

위 맥락을 참고하여 자연스럽게 응답하거나, 필요한 경우 분석/요약해주세요."""
    except Exception:
        return f"사용자의 요청: {current_text}\n\n이 요청에 대해 자연스럽게 대화하거나, 필요한 경우 분석/요약하여 응답해주세요."
