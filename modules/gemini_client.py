#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini AI Client Module
Centralized Gemini AI analysis for all modules
"""

import os
import logging
from typing import Optional

import google.generativeai as genai

logger = logging.getLogger(__name__)

# Environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


class GeminiClient:
    def __init__(self, api_key: str = None):
        """
        Initialize Gemini client
        """
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            logger.error("Gemini API key not provided!")
            return

        try:
            genai.configure(api_key=self.api_key)
            self.safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            self.model = genai.GenerativeModel(
                'gemini-2.5-pro',
                safety_settings=self.safety_settings
            )
            logger.info("Gemini client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Gemini client: {e}")
            self.model = None

    def analyze_text(self, text: str, prompt: str = None) -> str:
        """
        Analyze text with custom prompt
        """
        if not self.model:
            return "Gemini client not initialized."

        try:
            if prompt:
                full_prompt = f"{prompt}\n\n{text}"
            else:
                full_prompt = text

            response = self.model.generate_content(
                full_prompt,
                safety_settings=self.safety_settings
            )
            return response.text.strip()

        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            # Check for block reason
            try:
                if e.response.prompt_feedback.block_reason:
                    return "콘텐츠가 안전 정책에 의해 차단되었습니다."
            except AttributeError:
                pass
            return f"분석 중 오류가 발생했습니다: {str(e)}"

    def analyze_image(self, image_data: bytes, mime_type: str = "image/jpeg") -> str:
        """
        Analyze image with Gemini Vision
        """
        if not self.model:
            return "Gemini client not initialized."

        try:
            prompt = "이미지를 분석하고 자세히 설명해주세요. 주요 내용, 텍스트, 객체를 포함하여 설명해주세요."

            response = self.model.generate_content([
                prompt,
                {"mime_type": mime_type, "data": image_data}
            ], safety_settings=self.safety_settings)

            return response.text.strip()

        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return f"이미지 분석 중 오류가 발생했습니다: {str(e)}"

    def analyze_audio(self, audio_data: bytes, mime_type: str = "audio/wav") -> str:
        """
        Analyze/transcribe audio with Gemini
        """
        if not self.model:
            return "Gemini client not initialized."

        try:
            prompt = "이 오디오를 텍스트로 전사해주세요. 정확한 내용을 제공해주세요."

            response = self.model.generate_content([
                prompt,
                {"mime_type": mime_type, "data": audio_data}
            ], safety_settings=self.safety_settings)

            return response.text.strip()

        except Exception as e:
            logger.error(f"Error analyzing audio: {e}")
            return f"오디오 분석 중 오류가 발생했습니다: {str(e)}"

    def summarize_long_text(self, text: str, max_length: int = 500) -> str:
        """
        Summarize long text with character limit
        """
        if not self.model:
            return "Gemini client not initialized."

        try:
            prompt = f"""다음 텍스트를 {max_length}자 이내로 요약해주세요.
핵심 내용만 간결하게 정리해주세요.

텍스트:
{text}

요약:"""

            response = self.model.generate_content(prompt, safety_settings=self.safety_settings)
            return response.text.strip()

        except Exception as e:
            logger.error(f"Error summarizing text: {e}")
            return f"요약 중 오류가 발생했습니다: {str(e)}"

    def extract_key_points(self, text: str) -> str:
        """
        Extract key points from text
        """
        if not self.model:
            return "Gemini client not initialized."

        try:
            prompt = f"""다음 텍스트에서 핵심 포인트들을 추출해주세요.
각 포인트를bullet point 형식으로 정리해주세요.\n\n텍스트:\n{text}\n\n핵심 포인트:"""

            response = self.model.generate_content(prompt, safety_settings=self.safety_settings)
            return response.text.strip()

        except Exception as e:
            logger.error(f"Error extracting key points: {e}")
            return f"포인트 추출 중 오류가 발생했습니다: {str(e)}"

    def translate_text(self, text: str, target_language: str = "English") -> str:
        """
        Translate text to target language
        """
        if not self.model:
            return "Gemini client not initialized."

        try:
            prompt = f"""다음 텍스트를 {target_language}로 번역해주세요.
자연스럽고 정확한 번역을 제공해주세요.\n\n텍스트:\n{text}\n\n번역:"""

            response = self.model.generate_content(prompt, safety_settings=self.safety_settings)
            return response.text.strip()

        except Exception as e:
            logger.error(f"Error translating text: {e}")
            return f"번역 중 오류가 발생했습니다: {str(e)}"

    def analyze_sentiment(self, text: str) -> str:
        """
        Analyze sentiment of text
        """
        if not self.model:
            return "Gemini client not initialized."

        try:
            prompt = f"""다음 텍스트의 감정을 분석해주세요.
긍정/부정/중립과 주요 감정을 설명해주세요.\n\n텍스트:\n{text}\n\n감정 분석:"""

            response = self.model.generate_content(prompt, safety_settings=self.safety_settings)
            return response.text.strip()

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return f"감정 분석 중 오류가 발생했습니다: {str(e)}"


# Global instance
gemini_client = None


def get_gemini_client() -> GeminiClient:
    """
    Get or create global Gemini client instance
    """
    global gemini_client
    if gemini_client is None:
        gemini_client = GeminiClient()
    return gemini_client


# Convenience functions
def analyze_text(text: str, prompt: str = None) -> str:
    """Quick text analysis"""
    client = get_gemini_client()
    return client.analyze_text(text, prompt)


def analyze_image(image_data: bytes, mime_type: str = "image/jpeg") -> str:
    """Quick image analysis"""
    client = get_gemini_client()
    return client.analyze_image(image_data, mime_type)


def analyze_audio(audio_data: bytes, mime_type: str = "audio/wav") -> str:
    """Quick audio analysis"""
    client = get_gemini_client()
    return client.analyze_audio(audio_data, mime_type)


def summarize(text: str, max_length: int = 500) -> str:
    """Quick text summarization"""
    client = get_gemini_client()
    return client.summarize_long_text(text, max_length)


def extract_points(text: str) -> str:
    """Quick key point extraction"""
    client = get_gemini_client()
    return client.extract_key_points(text)


def translate(text: str, target_language: str = "English") -> str:
    """Quick translation"""
    client = get_gemini_client()
    return client.translate_text(text, target_language)


def analyze_sentiment(text: str) -> str:
    """Quick sentiment analysis"""
    client = get_gemini_client()
    return client.analyze_sentiment(text)

# === [AUTO-INJECT] safe gemini wrapper ===
from typing import Tuple, Dict, Any

def _is_blocked(resp_or_err: Any) -> Tuple[bool, str]:
    """
    Gemini 응답/예외에서 '안전 차단'을 최대한 정확히 감지.
    실제 SDK별 필드가 다를 수 있으므로 보수적으로 처리.
    리턴: (blocked, reason)
    """
    try:
        # google.generativeai 응답 객체
        # 1) prompt_feedback
        pf = getattr(resp_or_err, "prompt_feedback", None)
        if pf and getattr(pf, "block_reason", None):
            return True, str(pf.block_reason)
        # 2) finish_reason
        cand0 = getattr(resp_or_err, "candidates", [None])[0]
        fr = getattr(cand0, "finish_reason", None)
        if fr and str(fr).lower().find("safety") >= 0:
            return True, str(fr)
        # 3) safety_ratings 안에 "blocked" 유사 키워드가 있을 때
        sr = getattr(cand0, "safety_ratings", None)
        if sr:
            s = str(sr).lower()
            if "block" in s or "unsafe" in s:
                return True, "safety_ratings"
    except Exception:
        pass

    # 예외 객체에 safety/blocked 단어가 들어간 경우
    try:
        msg = str(resp_or_err).lower()
        if any(k in msg for k in ["safety", "blocked", "blocked_reason"]):
            return True, msg
    except Exception:
        pass

    return False, ""

# === [AUTO-INJECT] robust model selection ===
import google.generativeai as genai

_ALIASES = {
    "2.5-flash-lite": "gemini-2.5-flash-lite",
    "2.5-flash":      "gemini-2.5-flash-latest",
    "2.5-pro":        "gemini-2.5-pro-latest",
}

def _normalize(name: str) -> str:
    return _ALIASES.get(name.strip(), name.strip())

def _pick_supported(preferred: str, need="generateContent") -> str:
    want = _normalize(preferred)
    try:
        models = list(genai.list_models())
        # 완전 일치 + 메서드 지원
        for m in models:
            if m.name.endswith(want) and need in getattr(m, "supported_generation_methods", []):
                return m.name.replace("models/","")
        # 계열 매칭(앞부분 동일) 중 최신
        base = want.split("-latest")[0]
        cands = [m for m in models if base in m.name and need in getattr(m,"supported_generation_methods",[])]
        if cands:
            return sorted(cands, key=lambda x: x.name, reverse=True)[0].name.replace("models/","")
    except Exception:
        pass
    return want

def generate_text_safe(prompt: str, *, temperature: float = 0.2, max_tokens: int = 2048) -> Dict[str, Any]:
    """
    차단은 'blocked=True'로 명시하고, 일반 에러는 'error'로 구분해서 리턴.
    호출측은 메시지를 분기 처리 가능.
    """
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    order = ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro"]
    last_err = None
    for model_name in order:
        try:
            real_model_name = _pick_supported(model_name)
            logger.info(f"[Gemini] using model: {real_model_name} (requested='{model_name}')")
            model = genai.GenerativeModel(
                model_name=real_model_name, 
                safety_settings=safety_settings
            )
            resp = model.generate_content(
                prompt,
                generation_config={"temperature": temperature, "max_output_tokens": max_tokens},
            )
            blocked, reason = _is_blocked(resp)
            if blocked:
                return {"ok": False, "blocked": True, "reason": reason, "text": ""}
            text = ""
            try:
                text = getattr(resp, "text", None) or resp.candidates[0].content.parts[0].text
            except Exception:
                text = str(resp)
            return {"ok": True, "blocked": False, "reason": "", "text": text}
        except Exception as e:
            blocked, reason = _is_blocked(e)
            if blocked:
                return {"ok": False, "blocked": True, "reason": reason or str(e), "text": ""}
            last_err = e
            continue
    return {"ok": False, "blocked": False, "reason": str(last_err or "unknown"), "text": ""}
# === [/AUTO-INJECT] ===
# === [/AUTO-INJECT] ===