"""Gravity AI — Ollama Provider V13.0 PRO"""
import json
import time
import base64
from typing import Generator, List, Dict, Any, Optional
from providers.base import ProviderPlugin, ProviderResult
from providers.local._base_local import _http_get, _http_post_stream, _http_post, _safe_json

class OllamaProvider(ProviderPlugin):
    name             = "Ollama"
    protocol         = "ollama"
    category         = "local"
    default_port     = 11434
    supports_vision  = True
    supports_function_calling = False
    default_context  = 131072

    def check_health(self) -> ProviderResult:
        r   = self._make_result(f"http://localhost:{self.default_port}")
        t0  = time.time()
        data = _http_get(f"http://localhost:{self.default_port}/api/tags", timeout=0.9)
        r.response_ms = int((time.time() - t0) * 1000)
        if data and "models" in data:
            r.is_healthy = True
            r.models     = [{"name": m["name"], "size": m.get("size", 0)} for m in data["models"]]
            ps = _http_get(f"http://localhost:{self.default_port}/api/ps", timeout=0.5)
            if ps and ps.get("models"):
                r.active_model = ps["models"][0]["name"]
                r.supports_vision = any("llava" in m["name"] or "vision" in m["name"] or "moondream" in m["name"]
                                         for m in ps["models"])
        return r

    def _payload(self, messages: List[Dict[str, Any]], model: str, options: Dict[str, Any], stream: bool) -> Dict[str, Any]:
        p: Dict[str, Any] = {"model": model, "messages": messages, "stream": stream}
        valid = {"num_ctx", "temperature", "top_p", "top_k", "repeat_penalty", "seed", "num_predict"}
        opts  = {k: v for k, v in options.items() if k in valid}
        if opts:
            p["options"] = opts
        return p

    def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        model:    str,
        options:  Dict[str, Any],
    ) -> Generator[str, None, None]:
        url = f"http://localhost:{self.default_port}/api/chat"
        p   = self._payload(messages, model, options, True)
        for raw in _http_post_stream(url, p):
            d = _safe_json(raw)
            if d and "message" in d:
                chunk = d["message"].get("content", "")
                if chunk:
                    yield chunk

    def chat_complete(
        self,
        messages: List[Dict[str, Any]],
        model:    str,
        options:  Dict[str, Any],
    ) -> str:
        url = f"http://localhost:{self.default_port}/api/chat"
        p   = self._payload(messages, model, options, False)
        raw = _http_post(url, p)
        d   = _safe_json(raw)
        return d["message"]["content"] if d and "message" in d else ""

    def chat_stream_with_images(
        self,
        messages:    List[Dict[str, Any]],
        model:       str,
        options:     Dict[str, Any],
        image_paths: List[str],
    ) -> Generator[str, None, None]:
        images_b64: List[str] = []
        for path in image_paths:
            try:
                with open(path, "rb") as f:
                    images_b64.append(base64.b64encode(f.read()).decode())
            except Exception:
                pass
        # Inject images into last user message
        msgs = list(messages)
        if images_b64 and msgs and msgs[-1]["role"] == "user":
            msgs[-1] = dict(msgs[-1])
            msgs[-1]["images"] = images_b64
        url = f"http://localhost:{self.default_port}/api/chat"
        p   = self._payload(msgs, model, options, True)
        for raw in _http_post_stream(url, p):
            d = _safe_json(raw)
            if d and "message" in d:
                chunk = d["message"].get("content", "")
                if chunk:
                    yield chunk

