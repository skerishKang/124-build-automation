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
            self.model = genai.GenerativeModel('gemini-2.5-flash')
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

            response = self.model.generate_content(full_prompt)
            return response.text.strip()

        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
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
            ])

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
            ])

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

            response = self.model.generate_content(prompt)
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
각 포인트를bullet point 형식으로 정리해주세요.

텍스트:
{text}

핵심 포인트:"""

            response = self.model.generate_content(prompt)
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
자연스럽고 정확한 번역을 제공해주세요.

텍스트:
{text}

번역:"""

            response = self.model.generate_content(prompt)
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
긍정/부정/중립과 주요 감정을 설명해주세요.

텍스트:
{text}

감정 분석:"""

            response = self.model.generate_content(prompt)
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
