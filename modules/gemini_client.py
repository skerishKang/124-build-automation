"""
Provider-aware LLM client for text and vision generation.
Supports: Gemini (google-generativeai) and MiniMax (Anthropic-compatible API).
"""

import os
import base64
from typing import Dict, Any, List, Iterator

import google.generativeai as genai
import requests

try:
    import anthropic  # type: ignore
except Exception:
    anthropic = None


def _provider() -> str:
    return (os.getenv("LLM_PROVIDER", "gemini") or "gemini").lower()


def _gemini_model_name(default: str = "gemini-2.5-flash") -> str:
    return os.getenv("GEMINI_MODEL", default)


def _minimax_model_name(default: str = "claude-3-haiku-20240307") -> str:
    # MiniMax (Anthropic-compatible) models vary; allow override via env
    return os.getenv("MINIMAX_MODEL", default)


def _mk_anthropic_client():
    if not anthropic:
        raise RuntimeError("anthropic package not installed. Please `pip install anthropic`.")
    api_key = os.getenv("MINIMAX_API_TOKEN")
    base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/anthropic")
    if not api_key:
        raise RuntimeError("MINIMAX_API_TOKEN not set")
    return anthropic.Anthropic(api_key=api_key, base_url=base_url)


def _minimax_base_url() -> str:
    base = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/anthropic").rstrip("/")
    return base + "/v1/messages"


def _minimax_headers() -> Dict[str, str]:
    token = os.getenv("MINIMAX_API_TOKEN", "")
    if not token:
        raise RuntimeError("MINIMAX_API_TOKEN not set")
    version = os.getenv("ANTHROPIC_VERSION", "2023-06-01")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "anthropic-version": version,
    }


def generate_text_safe(prompt: str, temperature: float = 0.7, max_tokens: int = 1024) -> Dict[str, Any]:
    """Generate text safely with error handling (Gemini or MiniMax)."""
    try:
        if _provider() == "minimax":
            # Use direct HTTP to satisfy Authorization header requirement
            url = _minimax_base_url()
            headers = _minimax_headers()
            model_name = _minimax_model_name()
            payload = {
                "model": model_name,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "user", "content": [{"type": "text", "text": prompt}]}
                ],
            }
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=60)
                if resp.status_code != 200:
                    return {"ok": False, "text": "", "error": f"Error code: {resp.status_code} - {resp.text}"}
                data = resp.json()
                # Extract first text block
                content = data.get("content") or []
                text = ""
                for block in content:
                    if block.get("type") == "text" and block.get("text"):
                        text = block["text"]
                        break
                return {"ok": True, "text": text, "error": None}
            except Exception as e:
                return {"ok": False, "text": "", "error": str(e)}

        # Gemini path
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {"ok": False, "text": "", "error": "GEMINI_API_KEY not set"}
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(_gemini_model_name())
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )
        return {"ok": True, "text": response.text}
    except Exception as e:
        return {"ok": False, "text": "", "error": str(e)}


def generate_vision_safe(prompt: str, parts: List[Dict[str, Any]], *, temperature: float = 0.2, max_tokens: int = 2048) -> Dict[str, Any]:
    """Generate vision analysis safely with error handling (Gemini or MiniMax)."""
    try:
        if _provider() == "minimax":
            # Use direct HTTP with Authorization: Bearer <token>
            url = _minimax_base_url()
            headers = _minimax_headers()
            model_name = _minimax_model_name()
            content_blocks: List[Dict[str, Any]] = []
            for p in parts or []:
                mime = p.get("mime_type") or "image/jpeg"
                data = p.get("data") or b""
                b64 = base64.b64encode(data).decode("utf-8")
                content_blocks.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime,
                        "data": b64,
                    },
                })
            content_blocks.append({"type": "text", "text": prompt})
            payload = {
                "model": model_name,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "user", "content": content_blocks}
                ],
            }
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=60)
                if resp.status_code != 200:
                    return {"ok": False, "text": "", "error": f"Error code: {resp.status_code} - {resp.text}"}
                data = resp.json()
                content = data.get("content") or []
                text = ""
                for block in content:
                    if block.get("type") == "text" and block.get("text"):
                        text = block["text"]
                        break
                return {"ok": True, "text": text, "error": None}
            except Exception as e:
                return {"ok": False, "text": "", "error": str(e)}

        # Gemini path
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {"ok": False, "text": "", "error": "GEMINI_API_KEY not set"}
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(_gemini_model_name())
        contents = [prompt] + parts
        response = model.generate_content(
            contents,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )
        # Gracefully handle missing text
        text = ""
        try:
            text = getattr(response, "text", None) or response.candidates[0].content.parts[0].text
        except Exception:
            text = str(response)
        return {"ok": True, "text": text, "error": None}
    except Exception as e:
        return {"ok": False, "text": "", "error": str(e)}


def generate_text_stream(prompt: str, temperature: float = 0.7, max_tokens: int = 1024) -> Iterator[str]:
    """Yield partial text responses. For MiniMax, falls back to single-shot."""
    try:
        if _provider() == "minimax":
            # No streaming implemented for MiniMax here; yield once
            res = generate_text_safe(prompt, temperature=temperature, max_tokens=max_tokens)
            if res.get("ok") and res.get("text"):
                yield res["text"]
            return

        # Gemini streaming
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(_gemini_model_name())
        stream = model.generate_content(
            prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
            stream=True,
        )
        for chunk in stream:
            try:
                txt = getattr(chunk, "text", None)
                if txt:
                    yield txt
            except Exception:
                continue
    except Exception:
        return
