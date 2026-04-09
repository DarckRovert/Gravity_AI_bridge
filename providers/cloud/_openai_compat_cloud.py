"""
providers/cloud/_openai_compat_cloud.py — Base for all OpenAI-compatible cloud providers.
Internal (starts with _), not auto-discovered by registry.
"""
import json
import time
import urllib.request
import urllib.error
from typing import Generator

from providers.base import ProviderPlugin, ProviderResult
from core.key_manager import KeyManager


def _cloud_request_stream(url: str, payload: dict, headers: dict) -> Generator[str, None, None]:
    """Streams SSE from any OpenAI-compatible cloud endpoint. Yields content chunks."""
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=300) as r:
        for raw in r:
            line = raw.decode("utf-8", errors="ignore").strip()
            if not line.startswith("data:"):
                continue
            d_str = line[5:].strip()
            if d_str == "[DONE]":
                break
            try:
                d = json.loads(d_str)
                if "choices" in d and d["choices"]:
                    delta   = d["choices"][0].get("delta", {})
                    r_chunk = delta.get("reasoning_content", "")
                    chunk   = delta.get("content", "")
                    if r_chunk:
                        yield "<think>" + r_chunk + "</think>"
                    if chunk:
                        yield chunk
            except Exception:
                pass


def _cloud_request_complete(url: str, payload: dict, headers: dict) -> str:
    """Non-streaming cloud request. Returns full content string."""
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.loads(r.read().decode("utf-8"))
    if "choices" in d and d["choices"]:
        return d["choices"][0].get("message", {}).get("content", "")
    return ""


class OpenAICompatCloudProvider(ProviderPlugin):
    """
    Base class for all OpenAI-compatible cloud providers.
    Subclasses only need to set class attributes and optionally override
    _get_headers() if auth differs from standard Bearer token.
    """
    category              = "cloud"
    protocol              = "openai"
    requires_key          = True
    # Subclasses set these:
    _base_url:        str = ""
    _key_id:          str = ""   # Key in KeyManager (e.g. "groq", "mistral")
    _available_models: list[str] = []
    _chat_path:       str = "/chat/completions"

    def _get_api_key(self) -> str | None:
        return KeyManager.get_key(self._key_id)

    def _get_headers(self) -> dict:
        key = self._get_api_key() or "no-key"
        return {
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {key}",
        }

    def check_health(self) -> ProviderResult:
        r              = self._make_result(self._base_url)
        r.key_configured = KeyManager.has_key(self._key_id)
        if not r.key_configured:
            return r  # Cloud provider without key → not healthy
        # Populate static model list (no live scan needed for cloud)
        r.is_healthy = True
        r.models     = [{"name": m, "size": 0} for m in self._available_models]
        if r.models:
            r.active_model = r.models[0]["name"]
        return r

    def chat_stream(self, messages, model, options) -> Generator[str, None, None]:
        payload    = {"model": model, "messages": messages, "stream": True}
        for k in ("temperature", "top_p", "max_tokens"):
            if k in options:
                payload[k] = options[k]
        url     = f"{self._base_url.rstrip('/')}{self._chat_path}"
        headers = self._get_headers()
        yield from _cloud_request_stream(url, payload, headers)

    def chat_complete(self, messages, model, options) -> str:
        payload = {"model": model, "messages": messages, "stream": False}
        for k in ("temperature", "top_p", "max_tokens"):
            if k in options:
                payload[k] = options[k]
        url     = f"{self._base_url.rstrip('/')}{self._chat_path}"
        headers = self._get_headers()
        return _cloud_request_complete(url, payload, headers)
