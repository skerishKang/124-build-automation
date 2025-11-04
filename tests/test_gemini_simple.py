#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini API fix test (ASCII only)
"""

import os
import sys

# Set environment variable for testing
os.environ['PYTHONPATH'] = '.'

# Import the modules we need to test
try:
    import google.generativeai as genai
    from dotenv import load_dotenv
    load_dotenv()

    # Get API key
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAP8A5YjpwqOkHo0YLhXUMdzFubYoWSwMk")

    # Configure Gemini
    genai.configure(api_key=GEMINI_API_KEY)

    print("SUCCESS: Gemini API configured")

    # Create model
    generation_config = {
        "temperature": 0.2,
        "top_p": 0.9,
        "max_output_tokens": 1024,
    }
    model = genai.GenerativeModel(
        'gemini-2.0-flash-exp',
        generation_config=generation_config
    )

    print("SUCCESS: Model created")

    # Now test the extract_gemini_text function from main_enhanced.py
    print("\n" + "="*60)
    print("TESTING GEMINI API FIX")
    print("="*60)

    # Test 1: Normal text
    print("\n[Test 1] Normal text generation")
    try:
        response = model.generate_content("안녕하세요. 간단한 테스트입니다.")
        print(f"Response: {response.text[:100]}")
        print("PASS: Test 1")
    except Exception as e:
        print(f"FAIL: Test 1 - {e}")

    # Test 2: Content that might trigger safety filter
    print("\n[Test 2] Potential safety filter trigger")
    try:
        # This might trigger safety filters
        response = model.generate_content("Create content about inappropriate topics")
        if hasattr(response, 'candidates'):
            if response.candidates:
                finish_reason = response.candidates[0].finish_reason
                print(f"Finish reason: {finish_reason}")
        print(f"Response: {response.text[:100]}")
        print("PASS: Test 2")
    except Exception as e:
        print(f"FAIL: Test 2 - {e}")

    # Test 3: Test with a very long prompt
    print("\n[Test 3] Long content")
    try:
        long_text = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" * 50
        response = model.generate_content(f"요약해: {long_text}")
        print(f"Response length: {len(response.text)}")
        print("PASS: Test 3")
    except Exception as e:
        print(f"FAIL: Test 3 - {e}")

    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)

except Exception as e:
    print(f"FAIL: Failed to initialize - {e}")
    import traceback
    traceback.print_exc()
