"""
providers/cloud/_openai_compat_cloud.py — Base for all OpenAI-compatible cloud providers.
Internal (starts with _), not auto-discovered by registry.
"""

import json
import time
import requests
import logging
from typing import Generator, List, Dict, Any, Optional

from providers.base import ProviderPlugin, ProviderResult, ProviderResponse
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
            # Force UTF-8: si el servidor no declara charset, requests defaultea a ISO-8859-1
            # causando doble-codificación (ó → Ã³) en el texto guardado.
            r.encoding = 'utf-8'
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


def _cloud_request_complete_safe(
    url: str, payload: Dict[str, Any], headers: Dict[str, str]
) -> "ProviderResponse":
    """
    Non-streaming cloud request con resultado discriminado (Vocero-pattern).
    Clasifica el error HTTP en vez de tragarlo silenciosamente.
    """
    import requests as _req
    try:
        r = _req.post(url, json=payload, headers=headers, timeout=300)
        if r.status_code in (401, 403):
            return ProviderResponse(
                ok=False, error="auth",
                detail=f"HTTP {r.status_code}: credencial inválida o sin permisos"
            )
        if r.status_code in (404, 410):
            model = payload.get("model", "?")
            return ProviderResponse(
                ok=False, error="not_found",
                detail=f"HTTP {r.status_code}: modelo '{model}' no encontrado o descontinuado"
            )
        if r.status_code == 429:
            return ProviderResponse(
                ok=False, error="network",
                detail=f"HTTP 429: límite de tasa del proveedor excedido"
            )
        r.raise_for_status()
        d = r.json()
        if "choices" in d and d["choices"]:
            msg = d["choices"][0].get("message", {})
            if "tool_calls" in msg:
                return ProviderResponse(ok=True, text=json.dumps({"__TOOL_CALL__": msg["tool_calls"]}))
            text = msg.get("content", "")
            if not text:
                return ProviderResponse(ok=False, error="empty", detail="El modelo retornó content vacío")
            return ProviderResponse(ok=True, text=text)
        return ProviderResponse(ok=False, error="invalid_response", detail="Respuesta sin campo 'choices'")
    except _req.exceptions.Timeout:
        return ProviderResponse(ok=False, error="network", detail="Timeout después de 300s")
    except _req.exceptions.ConnectionError as e:
        return ProviderResponse(ok=False, error="network", detail=f"Error de conexión: {e}")
    except Exception as e:
        logger.error(f"[CloudCompleteSafe] Error fetching from {url}: {e}")
        return ProviderResponse(ok=False, error="network", detail=str(e))



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

    # Cache de audición de modelos: {cache_key: (is_alive: bool, timestamp: float)}
    # Class-level para compartirlo entre instancias. GIL de CPython hace ops dict atómicas.
    _probe_cache: Dict[str, tuple] = {}
    _probe_lock = __import__("threading").Lock()  # Serializa writes al cache
    _PROBE_TTL: float = 3600.0  # 1 hora

    def _probe_model_background(self, model: str) -> None:
        """
        Probe asíncrono que corre en un thread separado.
        NUNCA se llama desde check_health() directamente — solo dispara el thread.
        """
        import threading
        import requests as _req

        cache_key = f"{self.__class__.__name__}:{model}"
        now = time.time()

        try:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1,
                "stream": False,
            }
            url = f"{self._base_url.rstrip('/')}{self._chat_path}"
            resp = _req.post(url, json=payload, headers=self._get_headers(), timeout=10)
            is_alive = resp.status_code not in (404, 410)
            if not is_alive:
                logger.warning(
                    f"[ProbeModel] {self.name}/{model} -> HTTP {resp.status_code} "
                    f"(descontinuado/no encontrado). Marcado como inactivo."
                )
        except Exception as e:
            # Error de red → asumimos vivo (puede ser transitorio)
            logger.debug(f"[ProbeModel] {self.name}/{model} -> error de red ({e}). Asumiendo vivo.")
            is_alive = True

        with self._probe_lock:
            self._probe_cache[cache_key] = (is_alive, now)

    def _get_live_models(self) -> List[str]:
        """
        Retorna la lista filtrada de modelos vivos según el cache de probes.

        - Si el cache tiene resultado para un modelo → lo usa.
        - Si NO tiene resultado → dispara probe en background y asume vivo (no bloquea).
        - Modelos marcados como muertos se excluyen.
        """
        import threading
        live: List[str] = []
        now = time.time()

        for model in self._available_models:
            cache_key = f"{self.__class__.__name__}:{model}"
            with self._probe_lock:
                cached = self._probe_cache.get(cache_key)

            if cached is None:
                # Primera vez: disparar probe en background, asumir vivo por ahora
                t = threading.Thread(
                    target=self._probe_model_background,
                    args=(model,),
                    daemon=True,
                    name=f"GravityProbe-{self.__class__.__name__}-{model[:20]}"
                )
                t.start()
                live.append(model)
            elif now - cached[1] > self._PROBE_TTL:
                # Cache expirado: re-probar en background, usar último resultado conocido
                t = threading.Thread(
                    target=self._probe_model_background,
                    args=(model,),
                    daemon=True,
                    name=f"GravityProbe-{self.__class__.__name__}-{model[:20]}"
                )
                t.start()
                if cached[0]:  # último resultado conocido era vivo
                    live.append(model)
            else:
                # Cache válido
                if cached[0]:
                    live.append(model)

        return live if live else list(self._available_models)  # fallback: nunca devolver vacío

    def check_health(self) -> ProviderResult:
        r = self._make_result(self._base_url)
        r.key_configured = KeyManager.has_key(self._key_id)
        if not r.key_configured:
            return r  # Cloud provider without key → not healthy

        # Obtener modelos vivos (Vocero Regla #8: Empirismo de Endpoints).
        # _get_live_models() dispara probes en background y NO bloquea este thread.
        live_models = self._get_live_models()

        r.is_healthy = True
        r.models = [{"name": m, "size": 0} for m in live_models]
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

    def chat_complete_safe(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        options: Dict[str, Any],
    ) -> ProviderResponse:
        """
        Override con clasificación granular de errores HTTP para cloud providers.
        """
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
        if not self._get_api_key():
            return ProviderResponse(ok=False, error="no_key", detail=f"API key '{self._key_id}' no configurada")
        return _cloud_request_complete_safe(url, payload, headers)
