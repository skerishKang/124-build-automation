import os
import logging
from typing import Dict, Any

# Assuming generate_text_safe is available for intent detection
from modules.gemini_client import generate_text_safe

logger = logging.getLogger(__name__)

def detect_intent(text: str) -> str:
    """
    Detects the intent of the given text (chat or analyze).
    Uses Gemini AI to classify the intent.
    """
    if not text or not text.strip():
        return "chat" # Default to chat for empty text

    # Heuristic for short texts
    if len(text) < 50:
        return "chat"

    # Use Gemini for more complex intent detection
    prompt = (
        "다음 텍스트의 의도를 'chat' (대화) 또는 'analyze' (분석/요약) 중 하나로 분류해주세요. "
        "텍스트가 짧거나 일반적인 대화인 경우 'chat'으로, "
        "정보 추출, 요약, 상세 분석이 필요한 경우 'analyze'로 분류해주세요. "
        "다른 설명 없이 'chat' 또는 'analyze'만 응답해주세요.\n\n"
        f"텍스트: {text}\n\n의도:"
    )

    res = generate_text_safe(prompt, temperature=0.0, max_tokens=10) # Low temperature for deterministic output
    
    if res.get("ok"):
        intent = res["text"].strip().lower()
        if "analyze" in intent:
            return "analyze"
        return "chat" # Default to chat if not clearly analyze
    else:
        logger.error(f"Failed to detect intent: {res.get('reason', 'unknown error')}")
        return "chat" # Fallback to chat mode on error