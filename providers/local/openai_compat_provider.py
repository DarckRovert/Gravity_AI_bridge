"""Gravity AI — OpenAI-Compatible Local Providers V13.0 PRO
Includes: LM Studio, vLLM, TabbyAPI, Oobabooga, LocalAI, Xinference, Llamafile, Jan AI
All share the same OpenAI-compatible /v1/chat/completions endpoint.
"""

import time
from typing import Generator, List, Dict, Any, Optional
from providers.base import ProviderPlugin, ProviderResult
from providers.local._base_local import (
    _http_get,
    _openai_compat_stream,
    _openai_compat_complete,
    _build_openai_payload,
    filter_chat_models,
    pick_active_model,
)


class _OpenAICompatLocalProvider(ProviderPlugin):
    """Mixin for all OpenAI-compatible local providers."""

    category: str = "local"
    protocol: str = "openai"
    requires_key: bool = False
    _health_path: str = "/v1/models"
    _chat_path: str = "/v1/chat/completions"
    _last_working_url: Optional[str] = None

    def _base_url(self) -> str:
        if self._last_working_url:
            return self._last_working_url
        return f"http://localhost:{self.default_port}"

    def check_health(self) -> ProviderResult:
        t0 = time.time()
        url = self._base_url()
        r = self._make_result(url)
        data = _http_get(f"{url}{self._health_path}", timeout=0.9)
        r.response_ms = int((time.time() - t0) * 1000)
        if data and "data" in data:
            r.is_healthy = True
            all_models = [
                {"name": m.get("id", ""), "size": 0}
                for m in data["data"]
                if m.get("id")
            ]
            r.models = filter_chat_models(all_models)
            r.active_model = pick_active_model(r.models)
            self._last_working_url = url
        return r

    def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        options: Dict[str, Any],
    ) -> Generator[str, None, None]:
        p = _build_openai_payload(messages, model, options, True)
        yield from _openai_compat_stream(self._base_url(), self._chat_path, p)

    def chat_complete(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        options: Dict[str, Any],
    ) -> str:
        p = _build_openai_payload(messages, model, options, False)
        return _openai_compat_complete(self._base_url(), self._chat_path, p)


# ── Concrete local providers ──────────────────────────────────────────────────


class LMStudioProvider(_OpenAICompatLocalProvider):
    name: str = "LM Studio"
    default_port: int = 1234
    supports_vision: bool = True
    supports_function_calling: bool = True
    default_context: int = 131072
    _alt_ports: List[int] = [1234, 8080]

    def check_health(self) -> ProviderResult:
        for port in self._alt_ports:
            t0 = time.time()
            url = f"http://localhost:{port}"
            data = _http_get(f"{url}{self._health_path}", timeout=2.5)
            if data and "data" in data:
                r = self._make_result(url)
                r.is_healthy = True
                r.response_ms = int((time.time() - t0) * 1000)
                all_models = [
                    {"name": m.get("id", ""), "size": 0}
                    for m in data["data"]
                    if m.get("id")
                ]
                r.models = filter_chat_models(all_models)
                r.active_model = pick_active_model(r.models)
                self._last_working_url = url
                return r
        return self._make_result(f"http://localhost:{self.default_port}")

    def _base_url(self) -> str:
        if self._last_working_url:
            return self._last_working_url
        for port in self._alt_ports:
            data = _http_get(f"http://localhost:{port}/v1/models", timeout=2.5)
            if data:
                url = f"http://localhost:{port}"
                self._last_working_url = url
                return url
        return f"http://localhost:{self.default_port}"


class vLLMProvider(_OpenAICompatLocalProvider):
    name: str = "vLLM"
    default_port: int = 8000
    supports_vision: bool = True
    supports_function_calling: bool = True
    default_context: int = 131072


class TabbyAPIProvider(_OpenAICompatLocalProvider):
    name: str = "TabbyAPI"
    default_port: int = 5000
    supports_function_calling: bool = True

    def check_health(self) -> ProviderResult:
        t0 = time.time()
        url = self._base_url()
        r = self._make_result(url)
        data = _http_get(f"{url}/v1/model", timeout=0.9)
        r.response_ms = int((time.time() - t0) * 1000)
        if data and "id" in data:
            r.is_healthy = True
            r.active_model = data["id"]
            r.models = [{"name": data["id"], "size": 0}]
            if "parameters" in data and "max_seq_len" in data["parameters"]:
                r.max_context = data["parameters"]["max_seq_len"]
            self._last_working_url = url
        return r


class OobaboogaProvider(_OpenAICompatLocalProvider):
    name: str = "Oobabooga"
    default_port: int = 5000
    _alt_ports: List[int] = [5000, 5001]

    def check_health(self) -> ProviderResult:
        for port in self._alt_ports:
            url = f"http://localhost:{port}"
            data = _http_get(f"{url}/v1/models", timeout=0.8)
            if data and "data" in data:
                r = self._make_result(url)
                r.is_healthy = True
                all_models = [
                    {"name": m.get("id", ""), "size": 0}
                    for m in data["data"]
                    if m.get("id")
                ]
                r.models = filter_chat_models(all_models)
                r.active_model = pick_active_model(r.models)
                self._last_working_url = url
                return r
            model_data = _http_get(f"{url}/api/v1/model", timeout=0.5)
            if model_data and "result" in model_data:
                r = self._make_result(url)
                r.is_healthy = True
                r.active_model = model_data["result"]
                r.models = [{"name": model_data["result"], "size": 0}]
                self._last_working_url = url
                return r
        return self._make_result(f"http://localhost:{self.default_port}")

    def _base_url(self) -> str:
        if self._last_working_url:
            return self._last_working_url
        for port in self._alt_ports:
            data = _http_get(f"http://localhost:{port}/v1/models", timeout=0.5)
            if data:
                url = f"http://localhost:{port}"
                self._last_working_url = url
                return url
            model_data = _http_get(f"http://localhost:{port}/api/v1/model", timeout=0.5)
            if model_data and "result" in model_data:
                url = f"http://localhost:{port}"
                self._last_working_url = url
                return url
        return f"http://localhost:{self.default_port}"


class LocalAIProvider(_OpenAICompatLocalProvider):
    name: str = "LocalAI"
    default_port: int = 8080
    supports_vision: bool = True
    supports_function_calling: bool = True


class XinferenceProvider(_OpenAICompatLocalProvider):
    name: str = "Xinference"
    default_port: int = 9997

    def check_health(self) -> ProviderResult:
        t0 = time.time()
        url = self._base_url()
        r = self._make_result(url)
        data = _http_get(f"{url}/v1/models/running", timeout=0.9)
        r.response_ms = int((time.time() - t0) * 1000)
        if data is not None:
            r.is_healthy = True
            if isinstance(data, dict):
                r.models = [{"name": uid, "size": 0} for uid in data.keys()]
            elif isinstance(data, list):
                r.models = [
                    {"name": m.get("model_uid", m.get("id", "")), "size": 0}
                    for m in data
                ]
            if r.models:
                r.active_model = r.models[0]["name"]
            self._last_working_url = url
        return r


class LlamafileProvider(_OpenAICompatLocalProvider):
    name: str = "Llamafile"
    default_port: int = 8080
    _alt_ports: List[int] = [8080, 8081]

    def check_health(self) -> ProviderResult:
        for port in self._alt_ports:
            url = f"http://localhost:{port}"
            data = _http_get(f"{url}/v1/models", timeout=0.8)
            if data and "data" in data:
                r = self._make_result(url)
                r.is_healthy = True
                all_models = [
                    {"name": m.get("id", ""), "size": 0}
                    for m in data["data"]
                    if m.get("id")
                ]
                r.models = filter_chat_models(all_models)
                r.active_model = pick_active_model(r.models)
                self._last_working_url = url
                return r
        return self._make_result(f"http://localhost:{self.default_port}")

    def _base_url(self) -> str:
        if self._last_working_url:
            return self._last_working_url
        for port in self._alt_ports:
            data = _http_get(f"http://localhost:{port}/v1/models", timeout=0.5)
            if data:
                url = f"http://localhost:{port}"
                self._last_working_url = url
                return url
        return f"http://localhost:{self.default_port}"


class JanAIProvider(_OpenAICompatLocalProvider):
    name: str = "Jan AI"
    default_port: int = 1337


class KoboldCPPProvider(ProviderPlugin):
    name: str = "Kobold CPP"
    protocol: str = "openai"
    category: str = "local"
    default_port: int = 5001
    _last_working_url: Optional[str] = None

    def check_health(self) -> ProviderResult:
        t0 = time.time()
        url = self._base_url()
        r = self._make_result(url)
        data = _http_get(f"{url}/api/extra/true_max_context_length", timeout=0.5)
        if data is not None:
            r.is_healthy = True
            r.max_context = data if isinstance(data, int) else 4096
        else:
            compat = _http_get(f"{url}/v1/models", timeout=0.8)
            if compat and "data" in compat:
                r.is_healthy = True
                r.models = [
                    {"name": m.get("id", ""), "size": 0}
                    for m in compat["data"]
                    if m.get("id")
                ]
        r.response_ms = int((time.time() - t0) * 1000)
        mdata = _http_get(f"{url}/api/v1/model", timeout=0.5)
        if mdata and "result" in mdata:
            r.active_model = mdata["result"]
            if not r.models:
                r.models = [{"name": mdata["result"], "size": 0}]
        if r.is_healthy:
            self._last_working_url = url
        return r

    def _base_url(self) -> str:
        if self._last_working_url:
            return self._last_working_url
        return f"http://localhost:{self.default_port}"

    def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        options: Dict[str, Any],
    ) -> Generator[str, None, None]:
        p = _build_openai_payload(messages, model, options, True)
        yield from _openai_compat_stream(self._base_url(), "/v1/chat/completions", p)

    def chat_complete(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        options: Dict[str, Any],
    ) -> str:
        p = _build_openai_payload(messages, model, options, False)
        return _openai_compat_complete(self._base_url(), "/v1/chat/completions", p)


class LlamaServerProvider(_OpenAICompatLocalProvider):
    """llama.cpp HTTP server (raw, not through Ollama)."""

    name: str = "llama.cpp"
    default_port: int = 8080
    _alt_ports: List[int] = [8080, 8081, 9999]
    _health_path: str = "/health"

    def check_health(self) -> ProviderResult:
        for port in self._alt_ports:
            t0 = time.time()
            url = f"http://localhost:{port}"
            data = _http_get(f"{url}/health", timeout=0.6)
            if data and data.get("status") == "ok":
                r = self._make_result(url)
                r.is_healthy = True
                r.response_ms = int((time.time() - t0) * 1000)
                props = _http_get(f"{url}/props", timeout=0.5)
                if props:
                    mname = props.get("default_generation_settings", {}).get(
                        "model", "llama.cpp"
                    )
                    r.active_model = mname
                    r.models = [{"name": mname, "size": 0}]
                    r.max_context = props.get("default_generation_settings", {}).get(
                        "n_ctx", 4096
                    )
                self._last_working_url = url
                return r
        return self._make_result(f"http://localhost:{self.default_port}")

    def _base_url(self) -> str:
        if self._last_working_url:
            return self._last_working_url
        for port in self._alt_ports:
            data = _http_get(f"http://localhost:{port}/health", timeout=0.5)
            if data and data.get("status") == "ok":
                url = f"http://localhost:{port}"
                self._last_working_url = url
                return url
        return f"http://localhost:{self.default_port}"


class LemonadeProvider(_OpenAICompatLocalProvider):
    name: str = "Lemonade"
    default_port: int = 8000
    _alt_ports: List[int] = [8000, 8080, 13305]

    def check_health(self) -> ProviderResult:
        for port in self._alt_ports:
            url = f"http://localhost:{port}"
            data = _http_get(f"{url}/v1/models", timeout=0.8)
            if data and "data" in data:
                r = self._make_result(url)
                r.is_healthy = True
                all_models = [
                    {"name": m.get("id", ""), "size": 0}
                    for m in data["data"]
                    if m.get("id")
                ]
                r.models = filter_chat_models(all_models)
                r.active_model = pick_active_model(r.models)
                self._last_working_url = url
                return r
        return self._make_result(f"http://localhost:{self.default_port}")

    def _base_url(self) -> str:
        if self._last_working_url:
            return self._last_working_url
        for port in self._alt_ports:
            data = _http_get(f"http://localhost:{port}/v1/models", timeout=0.5)
            if data:
                url = f"http://localhost:{port}"
                self._last_working_url = url
                return url
        return f"http://localhost:{self.default_port}"


class FastFlowLMProvider(_OpenAICompatLocalProvider):
    """
    FastFlowLM — Motor de inferencia nativo para NPUs AMD Ryzen AI (XDNA).
    Expone la API OpenAI-compatible en el puerto 52625.
    Optimizado para Hawk Point (Ryzen 8700G) con DEV_1502.
    Inspirado en el patrón de health-check paralelo de Project N.O.M.A.D.
    """

    name: str = "FastFlowLM (NPU)"
    default_port: int = 52625
    supports_vision: bool = True
    supports_function_calling: bool = True
    default_context: int = 4096  # Restringido para evitar VRAM crash (0xc01e0009) en NPU
    _alt_ports: List[int] = [52625]

    def check_health(self) -> ProviderResult:
        t0 = time.time()
        url = f"http://localhost:{self.default_port}"
        r = self._make_result(url)
        # FLM puede tardar hasta 10 minutos cargando el modelo en la NPU la primera vez.
        # Usamos timeout extendido para no reportarlo como DOWN mientras carga.
        data = _http_get(f"{url}/v1/models", timeout=15.0)
        r.response_ms = int((time.time() - t0) * 1000)
        if data and "data" in data:
            r.is_healthy = True
            all_models = [
                {"name": m.get("id", ""), "size": 0}
                for m in data["data"]
                if m.get("id")
            ]
            r.models = all_models if all_models else [{"name": "llama3.2:1b", "size": 0}]
            r.active_model = r.models[0]["name"] if r.models else "llama3.2:1b"
            r.max_context = self.default_context
            self._last_working_url = url
        else:
            # Verificar si el proceso FLM está corriendo aunque el puerto no responda aún
            # (estado: cargando modelo en NPU)
            import socket as _sock
            try:
                _s = _sock.socket(_sock.AF_INET, _sock.SOCK_STREAM)
                _s.settimeout(1.0)
                _conn = _s.connect_ex(("127.0.0.1", self.default_port))
                _s.close()
                if _conn == 0:
                    # Puerto abierto pero /v1/models no respondió — FLM arrancando
                    r.is_healthy = True
                    r.models = [{"name": "llama3.2:1b", "size": 0}]
                    r.active_model = "llama3.2:1b (cargando NPU...)"
                    r.max_context = self.default_context
                    self._last_working_url = url
            except Exception:
                pass
        return r

    def _base_url(self) -> str:
        if self._last_working_url:
            return self._last_working_url
        return f"http://localhost:{self.default_port}"
