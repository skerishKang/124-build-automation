"""
Telegram utilities for message formatting and processing
"""

import re
from typing import Tuple

def format_ai_text(text: str) -> Tuple[str, str]:
    """Format AI response text for Telegram with proper markdown"""
    if not text:
        return "응답이 비어있습니다.", "Markdown"

    # Try to determine if markdown should be used
    # If text contains markdown elements, use MarkdownV2
    markdown_indicators = ['**', '*', '`', '_', '[', ']', '(', ')']
    use_markdown_v2 = any(indicator in text for indicator in markdown_indicators)

    # Clean up text for markdown
    # Escape special characters for MarkdownV2
    if use_markdown_v2:
        special_chars = ['.', '(', ')', '-', '+', '=', '{', '}', '[', ']', '!', '|', ':']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text, "MarkdownV2"
    else:
        return text, "Markdown"

def chunk_text(text: str, max_length: int = 4096) -> list:
    """Split text into chunks that fit within Telegram's message limit"""
    if not text:
        return []

    # Simple chunking by length
    chunks = []
    current_chunk = ""

    # Split by paragraphs first
    paragraphs = text.split('\n\n')

    for paragraph in paragraphs:
        # If adding this paragraph would exceed max length
        if len(current_chunk) + len(paragraph) + 2 > max_length:
            # Save current chunk if not empty
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

        # If single paragraph is too long, split by sentences
        if len(paragraph) > max_length:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            for sentence in sentences:
                if len(current_chunk) + len(sentence) + 1 > max_length:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sentence + " "
                else:
                    if current_chunk:
                        current_chunk += sentence + " "
                    else:
                        current_chunk = sentence + " "
        else:
            # Add paragraph to current chunk
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph

    # Add remaining chunk
    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def strip_html_tags(text: str) -> str:
    """Strip HTML tags from text"""
    if not text:
        return ""
    return re.sub(r'<[^>]+>', '', text)
