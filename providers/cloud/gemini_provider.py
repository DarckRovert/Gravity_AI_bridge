"""
Gravity AI — Google Gemini Provider V13.0 PRO

Gemini usa la Google Generative Language API (REST).
Convierte internamente el formato messages OpenAI al formato contents[]
de Gemini y normaliza el stream SSE de vuelta a chunks de texto.
Soporta contexto de hasta 2M tokens (Gemini 2.5 Pro).
"""

import json
import urllib.request
import urllib.error
import logging
from typing import Generator, List, Dict, Any, Tuple
from providers.base import ProviderPlugin, ProviderResult
from core.key_manager import KeyManager

logger = logging.getLogger("gravity")

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(ProviderPlugin):
    name: str = "Google Gemini"
    protocol: str = "gemini"
    category: str = "cloud"
    requires_key: bool = True
    supports_vision: bool = True
    supports_function_calling: bool = True
    default_context: int = 1000000
    _key_id: str = "gemini"
    _available_models: List[str] = [
        "gemini-2.5-pro-exp-03-25",
        "gemini-2.0-flash",
        "gemini-2.0-flash-thinking-exp-01-21",
        "gemini-1.5-pro-latest",
        "gemini-1.5-flash-latest",
    ]

    def _convert_messages(
        self, messages: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Converts OpenAI messages → (system_instruction, gemini_contents)."""
        system = ""
        contents: List[Dict[str, Any]] = []
        for m in messages:
            if m.get("role") == "system":
                system += str(m.get("content", "")) + "\n"
            else:
                role = "user" if m.get("role") == "user" else "model"
                contents.append(
                    {
                        "role": role,
                        "parts": [{"text": m.get("content", "")}],
                    }
                )
        return system.strip(), contents

    def check_health(self) -> ProviderResult:
        r = self._make_result(GEMINI_BASE)
        r.key_configured = KeyManager.has_key(self._key_id)
        if r.key_configured:
            r.is_healthy = True
            r.models = [{"name": m, "size": 0} for m in self._available_models]
            r.active_model = self._available_models[0]
        return r

    def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        options: Dict[str, Any],
    ) -> Generator[str, None, None]:
        try:
            key = KeyManager.get_key(self._key_id) or ""
            system, contents = self._convert_messages(messages)
            payload: Dict[str, Any] = {
                "contents": contents,
                "generationConfig": {
                    "maxOutputTokens": options.get("max_tokens", 8192),
                    "temperature": options.get("temperature", 0.7),
                },
            }
            if system:
                payload["systemInstruction"] = {"parts": [{"text": system}]}

            url = f"{GEMINI_BASE}/{model}:streamGenerateContent?alt=sse&key={key}"
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                url, data=data, headers={"Content-Type": "application/json"}
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
                                if text:
                                    yield text
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"[GeminiStream] Error in stream: {e}")
            yield f"\n\n[**SYSTEM ERROR**: Fallo crítico en Gemini. Error: {str(e)}]\n\n"

    def chat_complete(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        options: Dict[str, Any],
    ) -> str:
        try:
            key = KeyManager.get_key(self._key_id) or ""
            system, contents = self._convert_messages(messages)
            payload: Dict[str, Any] = {
                "contents": contents,
                "generationConfig": {
                    "maxOutputTokens": options.get("max_tokens", 8192),
                    "temperature": options.get("temperature", 0.7),
                },
            }
            if system:
                payload["systemInstruction"] = {"parts": [{"text": system}]}

            url = f"{GEMINI_BASE}/{model}:generateContent?key={key}"
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                url, data=data, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=300) as r:
                d = json.loads(r.read().decode())
            for cand in d.get("candidates", []):
                for part in cand.get("content", {}).get("parts", []):
                    if "text" in part:
                        return str(part["text"])
        except Exception as e:
            logger.error(f"[GeminiComplete] Error in chat_complete: {e}")
        return ""

    def get_cost_per_million_tokens(self, model: str) -> Dict[str, float]:
        costs = {
            "gemini-2.5-pro-exp-03-25": {"input": 1.25, "output": 10.00},
            "gemini-2.0-flash": {"input": 0.075, "output": 0.30},
            "gemini-1.5-pro-latest": {"input": 1.25, "output": 5.00},
            "gemini-1.5-flash-latest": {"input": 0.075, "output": 0.30},
        }
        return costs.get(model, {"input": 1.25, "output": 5.00})
