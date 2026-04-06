"""
providers/local/_base_local.py — Shared HTTP helper for local providers V7.1
Internal — not auto-discovered by registry (filename starts with _).
"""

import json
import time
import socket
import urllib.request
import urllib.error
from typing import Generator


def _http_get(url: str, timeout: float = 1.0) -> dict | None:
    """GET request returning parsed JSON, or None on any error."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GravityAI/7.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def _http_post_stream(
    url: str,
    payload: dict,
    timeout: float = 1800,
) -> Generator[bytes, None, None]:
    """POST JSON, yield raw response lines."""
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json", "User-Agent": "GravityAI/7.0"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        for line in r:
            yield line


def _http_post(url: str, payload: dict, timeout: float = 1800) -> bytes:
    """POST JSON, return full response bytes."""
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json", "User-Agent": "GravityAI/7.0"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _safe_json(raw: bytes | str) -> dict | None:
    try:
        return json.loads(raw)
    except Exception:
        return None


def _openai_compat_stream(
    base_url: str,
    path: str,
    payload: dict,
) -> Generator[str, None, None]:
    """
    Consumed by OpenAI-compatible local providers.
    Streams SSE lines and yields content string chunks.
    """
    url = f"{base_url.rstrip('/')}{path}"
    for raw_line in _http_post_stream(url, payload):
        line = raw_line.decode("utf-8", errors="ignore").strip()
        if not line.startswith("data:"):
            continue
        data_str = line[5:].strip()
        if data_str == "[DONE]":
            break
        d = _safe_json(data_str)
        if d and "choices" in d and d["choices"]:
            delta = d["choices"][0].get("delta", {})
            chunk = delta.get("content", "")
            r_chunk = delta.get("reasoning_content", "")
            if r_chunk:
                yield f"\x1b[90m{r_chunk}\x1b[0m"   # dim gray for reasoning
            if chunk:
                yield chunk


def _openai_compat_complete(
    base_url: str,
    path: str,
    payload: dict,
) -> str:
    """Non-streaming for OpenAI-compatible endpoints."""
    url  = f"{base_url.rstrip('/')}{path}"
    raw  = _http_post(url, payload)
    data = _safe_json(raw)
    if data and "choices" in data and data["choices"]:
        return data["choices"][0].get("message", {}).get("content", "")
    return ""


def _build_openai_payload(
    messages: list[dict],
    model:    str,
    options:  dict,
    stream:   bool,
) -> dict:
    payload: dict = {"model": model, "messages": messages, "stream": stream}
    for key in ("temperature", "top_p", "max_tokens"):
        if key in options:
            payload[key] = options[key]
    return payload
