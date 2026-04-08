"""Gravity AI — OpenAI-Compatible Local Providers V7.1
Includes: LM Studio, vLLM, TabbyAPI, Oobabooga, LocalAI, Xinference, Llamafile, Jan AI
All share the same OpenAI-compatible /v1/chat/completions endpoint.
"""
import json
import time
from typing import Generator
from providers.base import ProviderPlugin, ProviderResult
from providers.local._base_local import (
    _http_get, _openai_compat_stream, _openai_compat_complete,
    _build_openai_payload, filter_chat_models, pick_active_model,
)



class _OpenAICompatLocalProvider(ProviderPlugin):
    """Mixin for all OpenAI-compatible local providers."""
    category         = "local"
    protocol         = "openai"
    requires_key     = False
    _health_path     = "/v1/models"
    _chat_path       = "/v1/chat/completions"

    def _base_url(self) -> str:
        return f"http://localhost:{self.default_port}"

    def check_health(self) -> ProviderResult:
        t0   = time.time()
        url  = self._base_url()
        r    = self._make_result(url)
        data = _http_get(f"{url}{self._health_path}", timeout=0.9)
        r.response_ms = int((time.time() - t0) * 1000)
        if data and "data" in data:
            r.is_healthy = True
            all_models   = [{"name": m.get("id", ""), "size": 0} for m in data["data"] if m.get("id")]
            r.models     = filter_chat_models(all_models)
            r.active_model = pick_active_model(r.models)
        return r


    def chat_stream(self, messages, model, options) -> Generator[str, None, None]:
        p = _build_openai_payload(messages, model, options, True)
        yield from _openai_compat_stream(self._base_url(), self._chat_path, p)

    def chat_complete(self, messages, model, options) -> str:
        p = _build_openai_payload(messages, model, options, False)
        return _openai_compat_complete(self._base_url(), self._chat_path, p)


# ── Concrete local providers ──────────────────────────────────────────────────

class LMStudioProvider(_OpenAICompatLocalProvider):
    name             = "LM Studio"
    default_port     = 1234
    supports_vision  = True
    supports_function_calling = True
    default_context  = 131072
    _alt_ports       = [1234, 8080]

    def check_health(self) -> ProviderResult:
        for port in self._alt_ports:
            t0   = time.time()
            url  = f"http://localhost:{port}"
            data = _http_get(f"{url}{self._health_path}", timeout=0.8)
            if data and "data" in data:
                r             = self._make_result(url)
                r.is_healthy  = True
                r.response_ms = int((time.time() - t0) * 1000)
                all_models    = [{"name": m.get("id",""), "size": 0} for m in data["data"] if m.get("id")]
                r.models      = filter_chat_models(all_models)
                r.active_model = pick_active_model(r.models)
                return r
        return self._make_result(f"http://localhost:{self.default_port}")


    def _base_url(self):
        # Pick the port that responded last time
        for port in self._alt_ports:
            data = _http_get(f"http://localhost:{port}/v1/models", timeout=0.5)
            if data:
                return f"http://localhost:{port}"
        return f"http://localhost:{self.default_port}"


class vLLMProvider(_OpenAICompatLocalProvider):
    name             = "vLLM"
    default_port     = 8000
    supports_vision  = True
    supports_function_calling = True
    default_context  = 131072


class TabbyAPIProvider(_OpenAICompatLocalProvider):
    name             = "TabbyAPI"
    default_port     = 5000
    supports_function_calling = True

    def check_health(self) -> ProviderResult:
        t0   = time.time()
        url  = self._base_url()
        r    = self._make_result(url)
        # TabbyAPI: /v1/model gives current loaded model
        data = _http_get(f"{url}/v1/model", timeout=0.9)
        r.response_ms = int((time.time() - t0) * 1000)
        if data and "id" in data:
            r.is_healthy   = True
            r.active_model = data["id"]
            r.models       = [{"name": data["id"], "size": 0}]
            if "parameters" in data and "max_seq_len" in data["parameters"]:
                r.max_context = data["parameters"]["max_seq_len"]
        return r


class OobaboogaProvider(_OpenAICompatLocalProvider):
    name         = "Oobabooga"
    default_port = 5000
    _alt_ports   = [5000, 5001]

    def check_health(self) -> ProviderResult:
        for port in self._alt_ports:
            url  = f"http://localhost:{port}"
            data = _http_get(f"{url}/v1/models", timeout=0.8)
            if data and "data" in data:
                r             = self._make_result(url)
                r.is_healthy  = True
                all_models    = [{"name": m.get("id",""), "size": 0} for m in data["data"] if m.get("id")]
                r.models      = filter_chat_models(all_models)
                r.active_model = pick_active_model(r.models)
                return r
            # Also check native /api/v1/model endpoint
            model_data = _http_get(f"{url}/api/v1/model", timeout=0.5)
            if model_data and "result" in model_data:
                r             = self._make_result(url)
                r.is_healthy  = True
                r.active_model = model_data["result"]
                r.models      = [{"name": model_data["result"], "size": 0}]
                r._chat_path  = "/v1/chat/completions"
                return r
        return self._make_result(f"http://localhost:{self.default_port}")



class LocalAIProvider(_OpenAICompatLocalProvider):
    name             = "LocalAI"
    default_port     = 8080
    supports_vision  = True
    supports_function_calling = True


class XinferenceProvider(_OpenAICompatLocalProvider):
    name         = "Xinference"
    default_port = 9997

    def check_health(self) -> ProviderResult:
        t0   = time.time()
        url  = self._base_url()
        r    = self._make_result(url)
        # Xinference running models endpoint
        data = _http_get(f"{url}/v1/models/running", timeout=0.9)
        r.response_ms = int((time.time() - t0) * 1000)
        if data is not None:
            r.is_healthy = True
            if isinstance(data, dict):
                r.models = [{"name": uid, "size": 0} for uid in data.keys()]
            elif isinstance(data, list):
                r.models = [{"name": m.get("model_uid", m.get("id", "")), "size": 0} for m in data]
            if r.models:
                r.active_model = r.models[0]["name"]
        return r


class LlamafileProvider(_OpenAICompatLocalProvider):
    name             = "Llamafile"
    default_port     = 8080
    _alt_ports       = [8080, 8081]

    def check_health(self) -> ProviderResult:
        for port in self._alt_ports:
            url  = f"http://localhost:{port}"
            data = _http_get(f"{url}/v1/models", timeout=0.8)
            if data and "data" in data:
                r             = self._make_result(url)
                r.is_healthy  = True
                all_models    = [{"name": m.get("id",""), "size": 0} for m in data["data"] if m.get("id")]
                r.models      = filter_chat_models(all_models)
                r.active_model = pick_active_model(r.models)
                return r
        return self._make_result(f"http://localhost:{self.default_port}")



class JanAIProvider(_OpenAICompatLocalProvider):
    name         = "Jan AI"
    default_port = 1337


class KoboldCPPProvider(ProviderPlugin):
    name         = "Kobold CPP"
    protocol     = "openai"
    category     = "local"
    default_port = 5001

    def check_health(self) -> ProviderResult:
        t0  = time.time()
        url = f"http://localhost:{self.default_port}"
        r   = self._make_result(url)
        # KoboldCPP native model info
        data = _http_get(f"{url}/api/extra/true_max_context_length", timeout=0.5)
        if data is not None:
            r.is_healthy  = True
            r.max_context = data if isinstance(data, int) else 4096
        else:
            # Try OpenAI-compat endpoint
            compat = _http_get(f"{url}/v1/models", timeout=0.8)
            if compat and "data" in compat:
                r.is_healthy = True
                r.models     = [{"name": m.get("id",""), "size": 0} for m in compat["data"] if m.get("id")]
        r.response_ms = int((time.time() - t0) * 1000)
        # Get current loaded model name
        mdata = _http_get(f"{url}/api/v1/model", timeout=0.5)
        if mdata and "result" in mdata:
            r.active_model = mdata["result"]
            if not r.models:
                r.models = [{"name": mdata["result"], "size": 0}]
        return r

    def _base_url(self):
        return f"http://localhost:{self.default_port}"

    def chat_stream(self, messages, model, options) -> Generator[str, None, None]:
        p = _build_openai_payload(messages, model, options, True)
        yield from _openai_compat_stream(self._base_url(), "/v1/chat/completions", p)

    def chat_complete(self, messages, model, options) -> str:
        p = _build_openai_payload(messages, model, options, False)
        return _openai_compat_complete(self._base_url(), "/v1/chat/completions", p)


class LlamaServerProvider(_OpenAICompatLocalProvider):
    """llama.cpp HTTP server (raw, not through Ollama)."""
    name             = "llama.cpp"
    default_port     = 8080
    _alt_ports       = [8080, 8081, 9999]
    _health_path     = "/health"

    def check_health(self) -> ProviderResult:
        for port in self._alt_ports:
            t0  = time.time()
            url = f"http://localhost:{port}"
            data = _http_get(f"{url}/health", timeout=0.6)
            if data and data.get("status") == "ok":
                r             = self._make_result(url)
                r.is_healthy  = True
                r.response_ms = int((time.time() - t0) * 1000)
                # Get model info from /props
                props = _http_get(f"{url}/props", timeout=0.5)
                if props:
                    mname = props.get("default_generation_settings", {}).get("model", "llama.cpp")
                    r.active_model = mname
                    r.models       = [{"name": mname, "size": 0}]
                    r.max_context  = props.get("default_generation_settings", {}).get("n_ctx", 4096)
                return r
        return self._make_result(f"http://localhost:{self.default_port}")


class LemonadeProvider(_OpenAICompatLocalProvider):
    name         = "Lemonade"
    default_port = 8000
    _alt_ports   = [8000, 8080, 13305]

    def check_health(self) -> ProviderResult:
        for port in self._alt_ports:
            url  = f"http://localhost:{port}"
            data = _http_get(f"{url}/v1/models", timeout=0.8)
            if data and "data" in data:
                r             = self._make_result(url)
                r.is_healthy  = True
                all_models    = [{"name": m.get("id",""), "size": 0} for m in data["data"] if m.get("id")]
                r.models      = filter_chat_models(all_models)
                r.active_model = pick_active_model(r.models)
                return r
        return self._make_result(f"http://localhost:{self.default_port}")

