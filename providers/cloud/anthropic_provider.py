"""
Gravity AI — Anthropic Claude Provider V13.0 PRO

Anthropic usa su propio protocolo Messages API (no OpenAI-compatible).
Este provider convierte internamente el formato messages OpenAI
al formato de Anthropic y normaliza el stream de vuelta.
"""

import json
import urllib.request
import urllib.error
import logging
from typing import Generator, List, Dict, Any, Optional, Tuple
from providers.base import ProviderPlugin, ProviderResult
from core.key_manager import KeyManager

logger = logging.getLogger("gravity")

ANTHROPIC_API  = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VER  = "2023-06-01"
BETAS          = "interleaved-thinking-2025-01-05,output-128k-2025-02-19"


class AnthropicProvider(ProviderPlugin):
    name: str              = "Anthropic"
    protocol: str          = "anthropic"
    category: str          = "cloud"
    requires_key: bool      = True
    supports_vision: bool   = True
    supports_function_calling: bool = True
    default_context: int   = 200000
    _key_id: str           = "anthropic"
    _available_models: List[str] = [
        "claude-opus-4-5",
        "claude-sonnet-4-5",
        "claude-3-7-sonnet-20250219",
        "claude-3-5-haiku-20241022",
        "claude-3-5-sonnet-20241022",
        "claude-3-opus-20240229",
    ]

    def _headers(self) -> Dict[str, str]:
        return {
            "x-api-key":         KeyManager.get_key(self._key_id) or "",
            "anthropic-version": ANTHROPIC_VER,
            "anthropic-beta":    BETAS,
            "Content-Type":      "application/json",
        }

    def _convert_messages(self, messages: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
        """Splits OpenAI messages into (system_prompt, anthropic_messages)."""
        system = ""
        anthro: List[Dict[str, Any]] = []
        for m in messages:
            if m.get("role") == "system":
                system += str(m.get("content", "")) + "\n"
            else:
                anthro.append({"role": m.get("role"), "content": m.get("content")})
        return system.strip(), anthro

    def check_health(self) -> ProviderResult:
        r = self._make_result(ANTHROPIC_API)
        r.key_configured = KeyManager.has_key(self._key_id)
        if r.key_configured:
            r.is_healthy   = True
            r.models       = [{"name": m, "size": 0} for m in self._available_models]
            r.active_model = self._available_models[0]
        return r

    def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        model:    str,
        options:  Dict[str, Any],
    ) -> Generator[str, None, None]:
        system, anthro = self._convert_messages(messages)
        payload: Dict[str, Any] = {
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
        try:
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
        except Exception as e:
            logger.error(f"[AnthropicStream] Error in chat_stream: {e}")
            yield f"\n\n[**SYSTEM ERROR**: Fallo crítico en Anthropic. Error: {str(e)}]\n\n"
        finally:
            if thinking_open:
                yield "</think>\n\n"

    def chat_complete(
        self,
        messages: List[Dict[str, Any]],
        model:    str,
        options:  Dict[str, Any],
    ) -> str:
        try:
            system, anthro = self._convert_messages(messages)
            payload: Dict[str, Any] = {
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
            for block in d.get("content", []):
                if block.get("type") == "text":
                    return str(block["text"])
        except Exception as e:
            logger.error(f"[AnthropicComplete] Error in chat_complete: {e}")
        return ""

    def get_cost_per_million_tokens(self, model: str) -> Dict[str, float]:
        costs = {
            "claude-opus-4-5":          {"input": 15.00, "output": 75.00},
            "claude-sonnet-4-5":        {"input": 3.00,  "output": 15.00},
            "claude-3-5-haiku-20241022":{"input": 0.80,  "output": 4.00},
            "claude-3-5-sonnet-20241022":{"input": 3.00, "output": 15.00},
        }
        return costs.get(model, {"input": 3.00, "output": 15.00})
