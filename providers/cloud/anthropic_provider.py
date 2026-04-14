"""
Gravity AI — Anthropic Claude Provider V7.0

Anthropic usa su propio protocolo Messages API (no OpenAI-compatible).
Este provider convierte internamente el formato messages OpenAI
al formato de Anthropic y normaliza el stream de vuelta.
"""

import json
import urllib.request
from typing import Generator
from providers.base import ProviderPlugin, ProviderResult
from core.key_manager import KeyManager

ANTHROPIC_API  = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VER  = "2023-06-01"
# Beta: interleaved-thinking permite <think> blocks en respuesta
# output-128k-2025-02-19 habilita ventana de salida extendida para Claude Sonnet
BETAS          = "interleaved-thinking-2025-01-05,output-128k-2025-02-19"


class AnthropicProvider(ProviderPlugin):
    name              = "Anthropic"
    protocol          = "anthropic"
    category          = "cloud"
    requires_key      = True
    supports_vision   = True
    supports_function_calling = True
    default_context   = 200000
    _key_id           = "anthropic"
    _available_models = [
        "claude-opus-4-5",
        "claude-sonnet-4-5",
        "claude-3-7-sonnet-20250219",
        "claude-3-5-haiku-20241022",
        "claude-3-5-sonnet-20241022",
        "claude-3-opus-20240229",
    ]

    def _headers(self) -> dict:
        return {
            "x-api-key":         KeyManager.get_key(self._key_id) or "",
            "anthropic-version": ANTHROPIC_VER,
            "anthropic-beta":    BETAS,
            "Content-Type":      "application/json",
        }

    def _convert_messages(self, messages: list[dict]) -> tuple[str, list[dict]]:
        """Splits OpenAI messages into (system_prompt, anthropic_messages)."""
        system = ""
        anthro = []
        for m in messages:
            if m["role"] == "system":
                system += m["content"] + "\n"
            else:
                anthro.append({"role": m["role"], "content": m["content"]})
        return system.strip(), anthro

    def check_health(self) -> ProviderResult:
        r = self._make_result(ANTHROPIC_API)
        r.key_configured = KeyManager.has_key(self._key_id)
        if r.key_configured:
            r.is_healthy   = True
            r.models       = [{"name": m, "size": 0} for m in self._available_models]
            r.active_model = self._available_models[0]
        return r

    def chat_stream(self, messages, model, options) -> Generator[str, None, None]:
        system, anthro = self._convert_messages(messages)
        payload = {
            "model":      model,
            "messages":   anthro,
            "max_tokens": options.get("max_tokens", 8192),
            "stream":     True,
        }
        if system:
            payload["system"] = system
        if options.get("temperature") is not None:
            payload["temperature"] = options["temperature"]

        data = json.dumps(payload).encode()
        req  = urllib.request.Request(ANTHROPIC_API, data=data, headers=self._headers())
        thinking_open = False
        with urllib.request.urlopen(req, timeout=300) as r:
            for raw in r:
                line = raw.decode("utf-8", errors="ignore").strip()
                if not line.startswith("data:"):
                    continue
                d_str = line[5:].strip()
                try:
                    d    = json.loads(d_str)
                    etype = d.get("type", "")
                    if etype == "content_block_start":
                        block_type = d.get("content_block", {}).get("type", "")
                        if block_type == "thinking":
                            thinking_open = True
                            yield "<think>⚙ Pensando profundamente...\n"
                    elif etype == "content_block_stop":
                        if thinking_open:
                            thinking_open = False
                            yield "</think>\n\n"
                    elif etype == "content_block_delta":
                        delta = d.get("delta", {})
                        if delta.get("type") == "thinking_delta":
                            yield delta.get('thinking', '')
                        elif delta.get("type") == "text_delta":
                            yield delta.get("text", "")
                except Exception:
                    pass

    def chat_complete(self, messages, model, options) -> str:
        system, anthro = self._convert_messages(messages)
        payload = {
            "model":      model,
            "messages":   anthro,
            "max_tokens": options.get("max_tokens", 8192),
        }
        if system:
            payload["system"] = system
        data = json.dumps(payload).encode()
        req  = urllib.request.Request(ANTHROPIC_API, data=data, headers=self._headers())
        with urllib.request.urlopen(req, timeout=300) as r:
            d = json.loads(r.read().decode())
        # Extract first text block
        for block in d.get("content", []):
            if block.get("type") == "text":
                return block["text"]
        return ""

    def get_cost_per_million_tokens(self, model: str) -> dict:
        costs = {
            "claude-opus-4-5":          {"input": 15.00, "output": 75.00},
            "claude-sonnet-4-5":        {"input": 3.00,  "output": 15.00},
            "claude-3-5-haiku-20241022":{"input": 0.80,  "output": 4.00},
            "claude-3-5-sonnet-20241022":{"input": 3.00, "output": 15.00},
        }
        return costs.get(model, {"input": 3.00, "output": 15.00})
