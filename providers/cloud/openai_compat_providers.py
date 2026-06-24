"""
Gravity AI — All OpenAI-compatible Cloud Providers V13.0 PRO

Includes: OpenAI, Groq, Mistral, DeepSeek Cloud,
          Together AI, Fireworks AI, xAI/Grok, Perplexity.
Each class is 3-10 lines — base class handles everything else.
"""

import json
import os
import urllib.request
import threading
from typing import Generator, List, Dict, Any
from providers.cloud._openai_compat_cloud import OpenAICompatCloudProvider

_SETTINGS_LOCK = threading.RLock()


def _safe_read_settings() -> Dict[str, Any]:
    with _SETTINGS_LOCK:
        try:
            base = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            path = os.path.join(base, "_settings.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}


# ── OpenAI ────────────────────────────────────────────────────────────────────
class OpenAIProvider(OpenAICompatCloudProvider):
    name: str = "OpenAI"
    _base_url: str = "https://api.openai.com/v1"
    _key_id: str = "openai"
    supports_vision: bool = True
    supports_function_calling: bool = True
    default_context: int = 128000
    _available_models: List[str] = [
        "gpt-4o",
        "gpt-4o-mini",
        "o1",
        "o1-mini",
        "o3",
        "o3-mini",
        "o4-mini",
        "gpt-4-turbo",
    ]

    def get_cost_per_million_tokens(self, model: str) -> Dict[str, float]:
        costs = {
            "gpt-4o": {"input": 5.00, "output": 15.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "o1": {"input": 15.00, "output": 60.00},
            "o1-mini": {"input": 3.00, "output": 12.00},
            "o3": {"input": 10.00, "output": 40.00},
            "o3-mini": {"input": 1.10, "output": 4.40},
            "o4-mini": {"input": 1.10, "output": 4.40},
        }
        return costs.get(model, {"input": 5.00, "output": 15.00})


# ── Groq ──────────────────────────────────────────────────────────────────────
class GroqProvider(OpenAICompatCloudProvider):
    name: str = "Groq"
    _base_url: str = "https://api.groq.com/openai/v1"
    _key_id: str = "groq"
    supports_function_calling: bool = True
    default_context: int = 131072
    _available_models: List[str] = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "deepseek-r1-distill-llama-70b",
        "qwen-qwq-32b",
        "mistral-saba-24b",
        "gemma2-9b-it",
    ]

    def get_cost_per_million_tokens(self, model: str) -> Dict[str, float]:
        costs = {
            "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
            "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
            "deepseek-r1-distill-llama-70b": {"input": 0.75, "output": 0.99},
            "qwen-qwq-32b": {"input": 0.29, "output": 0.39},
        }
        return costs.get(model, {"input": 0.59, "output": 0.79})


# ── Mistral ───────────────────────────────────────────────────────────────────
class MistralProvider(OpenAICompatCloudProvider):
    name: str = "Mistral AI"
    _base_url: str = "https://api.mistral.ai/v1"
    _key_id: str = "mistral"
    supports_function_calling: bool = True
    default_context: int = 131072
    _available_models: List[str] = [
        "mistral-large-2",
        "mistral-small-3-1",
        "codestral-latest",
        "mistral-nemo",
        "open-mistral-nemo",
    ]

    def get_cost_per_million_tokens(self, model: str) -> Dict[str, float]:
        costs = {
            "mistral-large-2": {"input": 2.00, "output": 6.00},
            "mistral-small-3-1": {"input": 0.10, "output": 0.30},
            "codestral-latest": {"input": 0.30, "output": 0.90},
        }
        return costs.get(model, {"input": 2.00, "output": 6.00})


# ── DeepSeek Cloud ────────────────────────────────────────────────────────────
class DeepSeekCloudProvider(OpenAICompatCloudProvider):
    name: str = "DeepSeek Cloud"
    _base_url: str = "https://api.deepseek.com/v1"
    _key_id: str = "deepseek"
    supports_function_calling: bool = True
    default_context: int = 64000
    _available_models: List[str] = ["deepseek-chat", "deepseek-reasoner"]

    def get_cost_per_million_tokens(self, model: str) -> Dict[str, float]:
        costs = {
            "deepseek-chat": {"input": 0.27, "output": 1.10},
            "deepseek-reasoner": {"input": 0.55, "output": 2.19},
        }
        return costs.get(model, {"input": 0.27, "output": 1.10})


# ── Together AI ───────────────────────────────────────────────────────────────
class TogetherProvider(OpenAICompatCloudProvider):
    name: str = "Together AI"
    _base_url: str = "https://api.together.xyz/v1"
    _key_id: str = "together"
    supports_function_calling: bool = True
    default_context: int = 131072
    _available_models: List[str] = [
        "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "Qwen/Qwen2.5-72B-Instruct-Turbo",
        "deepseek-ai/DeepSeek-R1",
        "mistralai/Mixtral-8x22B-Instruct-v0.1",
        "google/gemma-2-27b-it",
    ]

    def get_cost_per_million_tokens(self, model: str) -> Dict[str, float]:
        costs = {
            "meta-llama/Llama-3.3-70B-Instruct-Turbo": {"input": 0.88, "output": 0.88},
            "Qwen/Qwen2.5-72B-Instruct-Turbo": {"input": 1.20, "output": 1.20},
            "deepseek-ai/DeepSeek-R1": {"input": 3.00, "output": 7.00},
        }
        return costs.get(model, {"input": 0.90, "output": 0.90})


# ── Fireworks AI ──────────────────────────────────────────────────────────────
class FireworksProvider(OpenAICompatCloudProvider):
    name: str = "Fireworks AI"
    _base_url: str = "https://api.fireworks.ai/inference/v1"
    _key_id: str = "fireworks"
    supports_function_calling: bool = True
    default_context: int = 131072
    _available_models: List[str] = [
        "accounts/fireworks/models/llama-v3p3-70b-instruct",
        "accounts/fireworks/models/qwen2p5-coder-32b-instruct",
        "accounts/fireworks/models/deepseek-r1",
        "accounts/fireworks/models/firefunction-v2",
        "accounts/fireworks/models/mixtral-8x22b-instruct",
    ]

    def get_cost_per_million_tokens(self, model: str) -> Dict[str, float]:
        return {"input": 0.90, "output": 0.90}


# ── xAI / Grok ───────────────────────────────────────────────────────────────
class xAIProvider(OpenAICompatCloudProvider):
    name: str = "xAI (Grok)"
    _base_url: str = "https://api.x.ai/v1"
    _key_id: str = "xai"
    supports_vision: bool = True
    supports_function_calling: bool = True
    default_context: int = 131072
    _available_models: List[str] = [
        "grok-3",
        "grok-3-mini",
        "grok-2-vision",
        "grok-beta",
    ]

    def get_cost_per_million_tokens(self, model: str) -> Dict[str, float]:
        costs = {
            "grok-3": {"input": 3.00, "output": 15.00},
            "grok-3-mini": {"input": 0.30, "output": 0.50},
            "grok-beta": {"input": 5.00, "output": 15.00},
        }
        return costs.get(model, {"input": 3.00, "output": 15.00})


# ── Perplexity ────────────────────────────────────────────────────────────────
class PerplexityProvider(OpenAICompatCloudProvider):
    name: str = "Perplexity"
    _base_url: str = "https://api.perplexity.ai"
    _key_id: str = "perplexity"
    _chat_path: str = "/chat/completions"
    default_context: int = 127072
    _available_models: List[str] = [
        "sonar-pro",
        "sonar-reasoning-pro",
        "sonar-deep-research",
        "sonar",
    ]

    def get_cost_per_million_tokens(self, model: str) -> Dict[str, float]:
        costs = {
            "sonar-pro": {"input": 3.00, "output": 15.00},
            "sonar-reasoning-pro": {"input": 2.00, "output": 8.00},
            "sonar": {"input": 1.00, "output": 1.00},
        }
        return costs.get(model, {"input": 3.00, "output": 15.00})

    def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        options: Dict[str, Any],
    ) -> Generator[str, None, None]:
        """Perplexity: append citations to final output if present."""
        payload: Dict[str, Any] = {"model": model, "messages": messages, "stream": True}
        for k in ("temperature", "top_p", "max_tokens"):
            if k in options:
                payload[k] = options[k]
        headers = self._get_headers()
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{self._base_url}/chat/completions", data=data, headers=headers
        )
        citations: List[str] = []
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                for raw in r:
                    line = raw.decode("utf-8", errors="ignore").strip()
                    if line.startswith("data:"):
                        d_str = line[5:].strip()
                        if d_str == "[DONE]":
                            break
                        try:
                            d = json.loads(d_str)
                            if not citations and "citations" in d:
                                citations = d["citations"]
                            if "choices" in d and d["choices"]:
                                chunk = (
                                    d["choices"][0].get("delta", {}).get("content", "")
                                )
                                if chunk:
                                    yield chunk
                        except Exception:
                            pass
        except Exception as e:
            import logging

            logging.getLogger("gravity").error(f"[PerplexityStream] Error: {e}")

        if citations:
            refs = "\n\n**Fuentes:**\n" + "\n".join(
                f"[{i+1}] {c}" for i, c in enumerate(citations[:5])
            )
            yield refs


# ── Nvidia NIM ────────────────────────────────────────────────────────────────
class NvidiaProvider(OpenAICompatCloudProvider):
    name: str = "Nvidia NIM"
    _base_url: str = "https://integrate.api.nvidia.com/v1"
    _key_id: str = "nvidia"
    supports_vision: bool = True
    supports_function_calling: bool = True
    default_context: int = 128000
    _available_models: List[str] = [
        "meta/llama-3.3-70b-instruct",
        "meta/llama-3.1-8b-instruct",
        "deepseek-ai/deepseek-v4-pro",
        "deepseek-ai/deepseek-v4-flash",
        "mistralai/mixtral-8x22b-instruct-v0.1",
    ]

    def get_cost_per_million_tokens(self, model: str) -> Dict[str, float]:
        return {"input": 1.00, "output": 1.00}


# ── OpenRouter ────────────────────────────────────────────────────────────────
class OpenRouterProvider(OpenAICompatCloudProvider):
    name: str = "OpenRouter"
    _base_url: str = "https://openrouter.ai/api/v1"
    _key_id: str = "openrouter"
    supports_vision: bool = True
    supports_function_calling: bool = True
    default_context: int = 128000
    _available_models: List[str] = [
        "google/gemini-2.5-flash",
        "google/gemini-2.5-pro",
        "meta-llama/llama-3.3-70b-instruct",
        "deepseek/deepseek-r1",
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4o-mini",
    ]

    def get_cost_per_million_tokens(self, model: str) -> Dict[str, float]:
        return {"input": 1.00, "output": 1.00}


# ── Universal AI ──────────────────────────────────────────────────────────────
class UniversalProvider(OpenAICompatCloudProvider):
    name: str = "Universal AI"
    _key_id: str = "universal"
    supports_vision: bool = True
    supports_function_calling: bool = True
    default_context: int = 128000

    @property
    def _base_url(self) -> str:
        try:
            from core.config_manager import config

            url = config.get("model.universal_base_url") or config.get(
                "universal_base_url"
            )
            if url:
                return str(url).strip()
        except Exception:
            pass
        settings = _safe_read_settings()
        return settings.get(
            "universal_base_url", "https://openrouter.ai/api/v1"
        ).strip()

    @property
    def _available_models(self) -> List[str]:
        try:
            from core.config_manager import config

            model = config.get("model.universal_model") or config.get("universal_model")
            if model:
                return [str(model).strip()]
        except Exception:
            pass
        settings = _safe_read_settings()
        return [settings.get("universal_model", "google/gemini-2.5-flash").strip()]

    def get_cost_per_million_tokens(self, model: str) -> Dict[str, float]:
        return {"input": 1.00, "output": 1.00}
