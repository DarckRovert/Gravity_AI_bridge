"""
Gravity AI — All OpenAI-compatible Cloud Providers V7.0

Includes: OpenAI, Groq, Mistral, DeepSeek Cloud,
          Together AI, Fireworks AI, xAI/Grok, Perplexity.
Each class is 3-10 lines — base class handles everything else.
"""

from providers.cloud._openai_compat_cloud import OpenAICompatCloudProvider


# ── OpenAI ────────────────────────────────────────────────────────────────────
class OpenAIProvider(OpenAICompatCloudProvider):
    name              = "OpenAI"
    _base_url         = "https://api.openai.com/v1"
    _key_id           = "openai"
    supports_vision   = True
    supports_function_calling = True
    default_context   = 128000
    _available_models = [
        "gpt-4o", "gpt-4o-mini", "o1", "o1-mini",
        "o3", "o3-mini", "o4-mini", "gpt-4-turbo",
    ]

    def get_cost_per_million_tokens(self, model: str) -> dict:
        costs = {
            "gpt-4o":       {"input": 5.00,  "output": 15.00},
            "gpt-4o-mini":  {"input": 0.15,  "output": 0.60},
            "o1":           {"input": 15.00, "output": 60.00},
            "o1-mini":      {"input": 3.00,  "output": 12.00},
            "o3":           {"input": 10.00, "output": 40.00},
            "o3-mini":      {"input": 1.10,  "output": 4.40},
            "o4-mini":      {"input": 1.10,  "output": 4.40},
        }
        return costs.get(model, {"input": 5.00, "output": 15.00})


# ── Groq ──────────────────────────────────────────────────────────────────────
class GroqProvider(OpenAICompatCloudProvider):
    name              = "Groq"
    _base_url         = "https://api.groq.com/openai/v1"
    _key_id           = "groq"
    supports_function_calling = True
    default_context   = 131072
    _available_models = [
        "llama-3.3-70b-versatile", "llama-3.1-8b-instant",
        "deepseek-r1-distill-llama-70b", "qwen-qwq-32b",
        "mistral-saba-24b", "gemma2-9b-it",
    ]

    def get_cost_per_million_tokens(self, model: str) -> dict:
        costs = {
            "llama-3.3-70b-versatile":       {"input": 0.59,  "output": 0.79},
            "llama-3.1-8b-instant":          {"input": 0.05,  "output": 0.08},
            "deepseek-r1-distill-llama-70b": {"input": 0.75,  "output": 0.99},
            "qwen-qwq-32b":                  {"input": 0.29,  "output": 0.39},
        }
        return costs.get(model, {"input": 0.59, "output": 0.79})


# ── Mistral ───────────────────────────────────────────────────────────────────
class MistralProvider(OpenAICompatCloudProvider):
    name              = "Mistral AI"
    _base_url         = "https://api.mistral.ai/v1"
    _key_id           = "mistral"
    supports_function_calling = True
    default_context   = 131072
    _available_models = [
        "mistral-large-2", "mistral-small-3-1",
        "codestral-latest", "mistral-nemo",
        "open-mistral-nemo",
    ]

    def get_cost_per_million_tokens(self, model: str) -> dict:
        costs = {
            "mistral-large-2":   {"input": 2.00, "output": 6.00},
            "mistral-small-3-1": {"input": 0.10, "output": 0.30},
            "codestral-latest":  {"input": 0.30, "output": 0.90},
        }
        return costs.get(model, {"input": 2.00, "output": 6.00})


# ── DeepSeek Cloud ────────────────────────────────────────────────────────────
class DeepSeekCloudProvider(OpenAICompatCloudProvider):
    name              = "DeepSeek Cloud"
    _base_url         = "https://api.deepseek.com/v1"
    _key_id           = "deepseek"
    supports_function_calling = True
    default_context   = 64000
    _available_models = ["deepseek-chat", "deepseek-reasoner"]

    def get_cost_per_million_tokens(self, model: str) -> dict:
        costs = {
            "deepseek-chat":     {"input": 0.27, "output": 1.10},
            "deepseek-reasoner": {"input": 0.55, "output": 2.19},
        }
        return costs.get(model, {"input": 0.27, "output": 1.10})


# ── Together AI ───────────────────────────────────────────────────────────────
class TogetherProvider(OpenAICompatCloudProvider):
    name              = "Together AI"
    _base_url         = "https://api.together.xyz/v1"
    _key_id           = "together"
    supports_function_calling = True
    default_context   = 131072
    _available_models = [
        "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "Qwen/Qwen2.5-72B-Instruct-Turbo",
        "deepseek-ai/DeepSeek-R1",
        "mistralai/Mixtral-8x22B-Instruct-v0.1",
        "google/gemma-2-27b-it",
    ]

    def get_cost_per_million_tokens(self, model: str) -> dict:
        costs = {
            "meta-llama/Llama-3.3-70B-Instruct-Turbo": {"input": 0.88, "output": 0.88},
            "Qwen/Qwen2.5-72B-Instruct-Turbo":         {"input": 1.20, "output": 1.20},
            "deepseek-ai/DeepSeek-R1":                  {"input": 3.00, "output": 7.00},
        }
        return costs.get(model, {"input": 0.90, "output": 0.90})


# ── Fireworks AI ──────────────────────────────────────────────────────────────
class FireworksProvider(OpenAICompatCloudProvider):
    name              = "Fireworks AI"
    _base_url         = "https://api.fireworks.ai/inference/v1"
    _key_id           = "fireworks"
    supports_function_calling = True
    default_context   = 131072
    _available_models = [
        "accounts/fireworks/models/llama-v3p3-70b-instruct",
        "accounts/fireworks/models/qwen2p5-coder-32b-instruct",
        "accounts/fireworks/models/deepseek-r1",
        "accounts/fireworks/models/firefunction-v2",
        "accounts/fireworks/models/mixtral-8x22b-instruct",
    ]

    def get_cost_per_million_tokens(self, model: str) -> dict:
        return {"input": 0.90, "output": 0.90}  # Variable, check fireworks.ai


# ── xAI / Grok ───────────────────────────────────────────────────────────────
class xAIProvider(OpenAICompatCloudProvider):
    name              = "xAI (Grok)"
    _base_url         = "https://api.x.ai/v1"
    _key_id           = "xai"
    supports_vision   = True
    supports_function_calling = True
    default_context   = 131072
    _available_models = ["grok-3", "grok-3-mini", "grok-2-vision", "grok-beta"]

    def get_cost_per_million_tokens(self, model: str) -> dict:
        costs = {
            "grok-3":      {"input": 3.00, "output": 15.00},
            "grok-3-mini": {"input": 0.30, "output": 0.50},
            "grok-beta":   {"input": 5.00, "output": 15.00},
        }
        return costs.get(model, {"input": 3.00, "output": 15.00})


# ── Perplexity ────────────────────────────────────────────────────────────────
class PerplexityProvider(OpenAICompatCloudProvider):
    name              = "Perplexity"
    _base_url         = "https://api.perplexity.ai"
    _key_id           = "perplexity"
    _chat_path        = "/chat/completions"
    default_context   = 127072
    _available_models = [
        "sonar-pro", "sonar-reasoning-pro",
        "sonar-deep-research", "sonar",
    ]

    def get_cost_per_million_tokens(self, model: str) -> dict:
        costs = {
            "sonar-pro":           {"input": 3.00, "output": 15.00},
            "sonar-reasoning-pro": {"input": 2.00, "output": 8.00},
            "sonar":               {"input": 1.00, "output": 1.00},
        }
        return costs.get(model, {"input": 3.00, "output": 15.00})

    def chat_stream(self, messages, model, options):
        """Perplexity: append citations to final output if present."""
        import json
        import urllib.request
        payload = {"model": model, "messages": messages, "stream": True}
        for k in ("temperature", "top_p", "max_tokens"):
            if k in options:
                payload[k] = options[k]
        headers  = self._get_headers()
        data     = json.dumps(payload).encode()
        req      = urllib.request.Request(
            f"{self._base_url}/chat/completions", data=data, headers=headers
        )
        citations = []
        with urllib.request.urlopen(req, timeout=300) as r:
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
                            chunk = d["choices"][0].get("delta", {}).get("content", "")
                            if chunk:
                                yield chunk
                    except Exception:
                        pass
        if citations:
            refs = "\n\n**Fuentes:**\n" + "\n".join(f"[{i+1}] {c}" for i, c in enumerate(citations[:5]))
            yield refs
