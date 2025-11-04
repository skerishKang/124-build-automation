#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram formatting helpers to safely use MarkdownV2
"""

import os
import re
import html
from telegram.helpers import escape_markdown


def escape_md(text: str) -> str:
    """Escape text for Telegram MarkdownV2."""
    if text is None:
        return ""
    return escape_markdown(text, version=2)


def bold(text: str) -> str:
    """Wrap text in MarkdownV2 bold safely."""
    return f"*{escape_md(text)}*"


def code(text: str) -> str:
    """Wrap text in MarkdownV2 inline code safely."""
    return f"`{escape_md(text)}`"


def md_to_html_basic(text: str) -> str:
    """Best-effort Markdown→HTML for Telegram HTML parse mode.
    Handles code blocks, inline code, bold/italics, and links.
    """
    if text is None:
        return ""

    s = str(text)

    # 1) Code blocks (``` ... ```)
    code_map = {}
    def _cb_repl(m):
        idx = len(code_map)
        content = m.group(1)
        code_map[idx] = html.escape(content)
        return f"{{CODEBLOCK_{idx}}}"
    s = re.sub(r"```\s*([\s\S]*?)\s*```", _cb_repl, s)

    # Escape HTML for the rest
    s = html.escape(s)

    # Inline code: `code`
    s = re.sub(r"`([^`]+)`", lambda m: f"<code>{html.escape(m.group(1))}</code>", s)

    # Bold: **text** or __text__
    s = re.sub(r"\*\*(.+?)\*\*", lambda m: f"<b>{m.group(1)}</b>", s, flags=re.DOTALL)
    s = re.sub(r"__(.+?)__", lambda m: f"<b>{m.group(1)}</b>", s, flags=re.DOTALL)

    # Italic: *text* or _text_ (conservative for '_')
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", lambda m: f"<i>{m.group(1)}</i>", s, flags=re.DOTALL)
    s = re.sub(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)", lambda m: f"<i>{m.group(1)}</i>", s, flags=re.DOTALL)

    # Links: [text](url)
    def _link_repl(m):
        text = m.group(1)
        url = m.group(2)
        return f"<a href=\"{html.escape(url)}\">{text}</a>"
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", _link_repl, s)

    # Restore code blocks
    for idx, content in code_map.items():
        s = s.replace(f"{{CODEBLOCK_{idx}}}", f"<pre><code>{content}</code></pre>")

    return s


def format_ai_text(text: str):
    """
    Return (formatted, parse_mode) for Telegram based on TG_ALLOW_AI_MARKDOWN.
    - If enabled, convert Markdown-ish to HTML and use parse_mode='HTML'.
    - Else, escape to MarkdownV2 and use parse_mode='MarkdownV2'.
    """
    allow = os.getenv("TG_ALLOW_AI_MARKDOWN", "").lower() in ("1", "true", "yes", "y")
    if allow:
        return md_to_html_basic(text), 'HTML'
    return escape_md(text), 'MarkdownV2'
