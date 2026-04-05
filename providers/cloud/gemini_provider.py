"""
Gravity AI — Google Gemini Provider V7.0

Gemini usa la Google Generative Language API (REST).
Convierte internamente el formato messages OpenAI al formato contents[]
de Gemini y normaliza el stream SSE de vuelta a chunks de texto.
Soporta contexto de hasta 2M tokens (Gemini 2.5 Pro).
"""

import json
import urllib.request
from typing import Generator
from providers.base import ProviderPlugin, ProviderResult
from key_manager import KeyManager

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(ProviderPlugin):
    name              = "Google Gemini"
    protocol          = "gemini"
    category          = "cloud"
    requires_key      = True
    supports_vision   = True
    supports_function_calling = True
    default_context   = 1000000
    _key_id           = "gemini"
    _available_models = [
        "gemini-2.5-pro-preview-03-25",
        "gemini-2.0-flash",
        "gemini-2.0-flash-thinking-exp",
        "gemini-1.5-pro-latest",
        "gemini-1.5-flash-latest",
    ]

    def _convert_messages(self, messages: list[dict]) -> tuple[str, list[dict]]:
        """Converts OpenAI messages → (system_instruction, gemini_contents)."""
        system = ""
        contents = []
        for m in messages:
            if m["role"] == "system":
                system += m["content"] + "\n"
            else:
                role = "user" if m["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": m["content"]}],
                })
        return system.strip(), contents

    def check_health(self) -> ProviderResult:
        r = self._make_result(GEMINI_BASE)
        r.key_configured = KeyManager.has_key(self._key_id)
        if r.key_configured:
            r.is_healthy   = True
            r.models       = [{"name": m, "size": 0} for m in self._available_models]
            r.active_model = self._available_models[0]
        return r

    def chat_stream(self, messages, model, options) -> Generator[str, None, None]:
        key   = KeyManager.get_key(self._key_id) or ""
        system, contents = self._convert_messages(messages)
        payload: dict = {
            "contents":           contents,
            "generationConfig": {
                "maxOutputTokens": options.get("max_tokens", 8192),
                "temperature":     options.get("temperature", 0.7),
            },
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        url  = f"{GEMINI_BASE}/{model}:streamGenerateContent?alt=sse&key={key}"
        data = json.dumps(payload).encode()
        req  = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=300) as r:
            for raw in r:
                line = raw.decode("utf-8", errors="ignore").strip()
                if not line.startswith("data:"):
                    continue
                d_str = line[5:].strip()
                try:
                    d = json.loads(d_str)
                    for cand in d.get("candidates", []):
                        for part in cand.get("content", {}).get("parts", []):
                            text = part.get("text", "")
                            # Gemini thinking-models put reasoning in <think> blocks sometimes
                            if text:
                                yield text
                except Exception:
                    pass

    def chat_complete(self, messages, model, options) -> str:
        key   = KeyManager.get_key(self._key_id) or ""
        system, contents = self._convert_messages(messages)
        payload: dict = {
            "contents":           contents,
            "generationConfig": {
                "maxOutputTokens": options.get("max_tokens", 8192),
                "temperature":     options.get("temperature", 0.7),
            },
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        url  = f"{GEMINI_BASE}/{model}:generateContent?key={key}"
        data = json.dumps(payload).encode()
        req  = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=300) as r:
            d = json.loads(r.read().decode())
        for cand in d.get("candidates", []):
            for part in cand.get("content", {}).get("parts", []):
                if "text" in part:
                    return part["text"]
        return ""

    def get_cost_per_million_tokens(self, model: str) -> dict:
        costs = {
            "gemini-2.5-pro-preview-03-25": {"input": 1.25, "output": 10.00},
            "gemini-2.0-flash":             {"input": 0.075, "output": 0.30},
            "gemini-1.5-pro-latest":        {"input": 1.25,  "output": 5.00},
            "gemini-1.5-flash-latest":      {"input": 0.075, "output": 0.30},
        }
        return costs.get(model, {"input": 1.25, "output": 5.00})
