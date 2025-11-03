# === [AUTO-INJECT] intent router ===
import re

ANALYZE_HINTS = [
    "요약", "분석", "정리", "핵심", "bullet", "map-reduce",
    "표로", "키포인트", "action item", "액션 아이템",
    "category", "주요 내용", "한줄 요약", "문서 분석",
]
CHAT_HINTS = [
    "안녕", "hello", "ㅎㅇ", "하이", "고마워", "뭐해", "대화", "잡담",
]

def detect_intent(text: str) -> str:
    """
    return: 'chat' | 'analyze' | 'auto'
    - 규칙:
      1) 명령 프리픽스 우선 (/analyze, /chat, /auto)
      2) 매우 짧은 입력(<= 80자) + 챗 힌트 → chat
      3) 긴 입력(>= 300자) 또는 분석 힌트 포함 → analyze
      4) 그 외 → chat
    """
    t = (text or "").strip().lower()
    if t.startswith("/analyze"): return "analyze"
    if t.startswith("/chat"):    return "chat"
    if t.startswith("/auto"):    return "auto"

    if len(t) <= 80 and any(h in t for h in [h.lower() for h in CHAT_HINTS]):
        return "chat"
    if len(t) >= 300 or any(h in t for h in [h.lower() for h in ANALYZE_HINTS]):
        return "analyze"
    return "chat"
# === [/AUTO-INJECT] ===
