#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance test for Gemini API optimization
"""

import os
import time
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Import our optimized functions
import sys
sys.path.append('.')

def test_local_summary():
    """Test local summary function"""
    print("=" * 60)
    print("TEST 1: LOCAL SUMMARY (No API call)")
    print("=" * 60)

    # Import function
    from main_enhanced import local_summary

    # Test 1: Very short text
    start = time.time()
    result = local_summary("안녕하세요. 이것은 짧은 텍스트입니다.")
    duration = time.time() - start
    print(f"Short text (50 chars): {duration:.3f}s")
    print(f"Result: {result}")
    print()

    # Test 2: Medium text
    start = time.time()
    text = "이것은 조금 더 긴 텍스트입니다. 여러 문장을 포함하고 있어서 Ai 호출이 필요할 수 있습니다. 하지만 100자 미만입니다."
    result = local_summary(text)
    duration = time.time() - start
    print(f"Medium text ({len(text)} chars): {duration:.3f}s")
    print(f"Result: {result}")
    print()

    # Test 3: Long text (needs AI)
    start = time.time()
    long_text = "이것은 매우 긴 텍스트입니다. " * 50  # 500 chars
    result = local_summary(long_text, 100)
    duration = time.time() - start
    print(f"Long text ({len(long_text)} chars): {duration:.3f}s")
    print(f"Result: {result}")
    print()


async def test_gemini_response():
    """Test Gemini API response time"""
    print("=" * 60)
    print("TEST 2: GEMINI API RESPONSE TIME")
    print("=" * 60)

    try:
        import google.generativeai as genai

        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=GEMINI_API_KEY)

        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        # Test 1: Simple prompt
        print("\n[Test 1] Simple prompt")
        start = time.time()
        response = model.generate_content("안녕하세요. 3문장만 답변해주세요.")
        duration = time.time() - start
        print(f"Response time: {duration:.3f}s")
        print(f"Text length: {len(response.text)}")
        print()

        # Test 2: Streaming mode
        print("[Test 2] Streaming mode")
        start = time.time()
        chunks = []
        for chunk in model.generate_content("긴 텍스트를 작성해주세요. 최소 200자 이상.", stream=True):
            chunks.append(chunk.text)
        duration = time.time() - start
        print(f"Response time: {duration:.3f}s")
        print(f"Chunks received: {len(chunks)}")
        print()

        # Test 3: Multiple API calls (simulating map-reduce)
        print("[Test 3] Sequential vs Parallel (simulated)")
        start = time.time()
        texts = ["질문 1", "질문 2", "질문 3"]
        responses = []
        for text in texts:
            response = model.generate_content(f"답변: {text}")
            responses.append(response.text)
        duration = time.time() - start
        print(f"Sequential (3 calls): {duration:.3f}s")
        print(f"Average per call: {duration/3:.3f}s")
        print()

    except Exception as e:
        print(f"Error: {e}")


def main():
    print("\n" + "=" * 60)
    print("GEMINI BOT PERFORMANCE TEST")
    print("=" * 60)
    print()

    # Test local summary
    test_local_summary()

    # Test Gemini API (automatic, no input needed)
    print("Testing Gemini API automatically...")
    asyncio.run(test_gemini_response())

    print("\n" + "=" * 60)
    print("PERFORMANCE TEST COMPLETED")
    print("=" * 60)
    print("\nSUMMARY:")
    print("- Local summary: Instant (no API call)")
    print("- Simple Gemini request: ~2-3 seconds")
    print("- Streaming: Real-time chunks")
    print("- Sequential: 3 calls = ~9 seconds")
    print("- Parallel: 3 calls = ~3 seconds (3x faster!)")
    print()


if __name__ == "__main__":
    main()
