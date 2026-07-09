"""
providers/cloud/_openai_compat_cloud.py — Base for all OpenAI-compatible cloud providers.
Internal (starts with _), not auto-discovered by registry.
"""

import json
import requests
import logging
from typing import Generator, List, Dict, Any, Optional

from providers.base import ProviderPlugin, ProviderResult
from core.key_manager import KeyManager

logger = logging.getLogger("gravity")


def _cloud_request_stream(
    url: str, payload: Dict[str, Any], headers: Dict[str, str]
) -> Generator[str, None, None]:
    """Streams SSE from any OpenAI-compatible cloud endpoint."""
    tool_calls_accumulator = {}
    
    try:
        with requests.post(
            url, json=payload, headers=headers, stream=True, timeout=300
        ) as r:
            r.raise_for_status()
            for line in r.iter_lines(decode_unicode=True):
                if not line:
                    continue
                line = line.strip()
                if not line.startswith("data:"):
                    continue
                d_str = line[5:].strip()
                if d_str == "[DONE]":
                    break
                try:
                    d = json.loads(d_str)
                    if "choices" in d and d["choices"]:
                        delta = d["choices"][0].get("delta", {})
                        
                        # Handle tool calls streaming
                        if "tool_calls" in delta:
                            for tc in delta["tool_calls"]:
                                idx = tc.get("index", 0)
                                if idx not in tool_calls_accumulator:
                                    tool_calls_accumulator[idx] = {"id": tc.get("id", ""), "type": "function", "function": {"name": "", "arguments": ""}}
                                if "id" in tc and tc["id"]:
                                    tool_calls_accumulator[idx]["id"] = tc["id"]
                                if "function" in tc:
                                    f = tc["function"]
                                    if "name" in f and f["name"]:
                                        tool_calls_accumulator[idx]["function"]["name"] += f["name"]
                                    if "arguments" in f and f["arguments"]:
                                        tool_calls_accumulator[idx]["function"]["arguments"] += f["arguments"]
                                continue
                                
                        r_chunk = delta.get("reasoning_content", "")
                        chunk = delta.get("content", "")
                        if r_chunk:
                            yield "<think>" + r_chunk + "</think>"
                        if chunk:
                            yield chunk
                except Exception:
                    pass
            
            # If we accumulated tool calls, yield them as a special JSON string at the end
            if tool_calls_accumulator:
                tool_calls_list = [tool_calls_accumulator[i] for i in sorted(tool_calls_accumulator.keys())]
                yield json.dumps({"__TOOL_CALLS__": tool_calls_list})
                
    except Exception as e:
        logger.error(f"[CloudStream] Error streaming from {url}: {e}")
        err_msg = f"\n\n[**SYSTEM ERROR**: Fallo crítico de conexión con la nube. Error: {str(e)}]\n\n"
        # Ensure the frontend can parse the error message immediately
        yield err_msg

def _cloud_request_complete(
    url: str, payload: Dict[str, Any], headers: Dict[str, str]
) -> str:
    """Non-streaming cloud request using requests library."""
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=300)
        r.raise_for_status()
        d = r.json()
        if "choices" in d and d["choices"]:
            msg = d["choices"][0].get("message", {})
            if "tool_calls" in msg:
                return json.dumps({"__TOOL_CALL__": msg["tool_calls"]})
            return msg.get("content", "")
    except Exception as e:
        logger.error(f"[CloudComplete] Error fetching from {url}: {e}")
    return ""


class OpenAICompatCloudProvider(ProviderPlugin):
    """
    Base class for all OpenAI-compatible cloud providers.
    Subclasses only need to set class attributes and optionally override
    _get_headers() if auth differs from standard Bearer token.
    """

    category: str = "cloud"
    protocol: str = "openai"
    requires_key: bool = True
    # Subclasses set these:
    _base_url: str = ""
    _key_id: str = ""  # Key in KeyManager (e.g. "groq", "mistral")
    _available_models: List[str] = []
    _chat_path: str = "/chat/completions"

    def _get_api_key(self) -> Optional[str]:
        return KeyManager.get_key(self._key_id)

    def _get_headers(self) -> Dict[str, str]:
        key = self._get_api_key() or "no-key"
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        }

    def check_health(self) -> ProviderResult:
        r = self._make_result(self._base_url)
        r.key_configured = KeyManager.has_key(self._key_id)
        if not r.key_configured:
            return r  # Cloud provider without key → not healthy
        # Populate static model list (no live scan needed for cloud)
        r.is_healthy = True
        r.models = [{"name": m, "size": 0} for m in self._available_models]
        if r.models:
            r.active_model = r.models[0]["name"]
        return r

    def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        options: Dict[str, Any],
    ) -> Generator[str, None, None]:
        payload: Dict[str, Any] = {"model": model, "messages": messages, "stream": True}
        for k in ("temperature", "top_p", "max_tokens", "tools", "tool_choice", "stop"):
            if k in options:
                payload[k] = options[k]
        url = f"{self._base_url.rstrip('/')}{self._chat_path}"
        headers = self._get_headers()
        yield from _cloud_request_stream(url, payload, headers)

    def chat_complete(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        options: Dict[str, Any],
    ) -> str:
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        for k in ("temperature", "top_p", "max_tokens", "tools", "tool_choice", "stop"):
            if k in options:
                payload[k] = options[k]
        url = f"{self._base_url.rstrip('/')}{self._chat_path}"
        headers = self._get_headers()
        return _cloud_request_complete(url, payload, headers)
