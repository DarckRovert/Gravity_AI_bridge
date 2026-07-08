"""
providers/local/_base_local.py — Shared HTTP helper for local providers V13.0 PRO
Internal — not auto-discovered by registry (filename starts with _).
"""

import json
import urllib.request
import urllib.error
from typing import Generator, List, Dict, Any, Optional


def _http_get(url: str, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
    """GET request returning parsed JSON, or None on any error."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GravityAI/7.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


# Patrones de nombre que identifican modelos NO aptos para chat.
# Corresponden a modelos de embeddings, rerankers, clasificadores o moderación.
_NON_CHAT_PATTERNS = (
    "embed",
    "embedding",
    "rerank",
    "reranker",
    "classifier",
    "moderation",
    "nomic-embed",
    "text-embedding",
    "bge-",
    "e5-",
    "gte-",
    "instructor-",
    "sentence-",
    "all-minilm",
    "clip",
    "whisper",
    "tts",
    "vision-encoder",
)


def is_chat_model(model_id: str) -> bool:
    """
    Retorna True si el modelo es apto para chat/completion.
    Retorna False si es un modelo de embeddings, reranker u otro no-chat.
    Comparación insensible a mayúsculas y -/_ .
    """
    normalized = model_id.lower().replace("-", "").replace("_", "").replace(".", "")
    for pat in _NON_CHAT_PATTERNS:
        pat_norm = pat.lower().replace("-", "").replace("_", "")
        if pat_norm in normalized:
            return False
    return True


def filter_chat_models(models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filtra una lista de {name, size} devolviendo solo los modelos aptos para chat.
    Si NINGUNO es apto (situación improbable), devuelve la lista original completa
    para no dejar el provider sin modelos.
    """
    chat_only = [m for m in models if is_chat_model(m.get("name", ""))]
    return chat_only if chat_only else models


def pick_active_model(models: List[Dict[str, Any]]) -> Optional[str]:
    """
    Elige el mejor modelo activo de una lista priorizando modelos de chat.
    Retorna el name del primero apto o None si la lista está vacía.
    """
    if not models:
        return None
    chat = filter_chat_models(models)
    return chat[0]["name"] if chat else models[0]["name"]


def _http_post_stream(
    url: str,
    payload: dict,
    timeout: float = 300.0,
) -> Generator[bytes, None, None]:
    """POST JSON, yield raw response lines with safe execution timeouts."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "GravityAI/7.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            for line in r:
                yield line
    except urllib.error.HTTPError as e:
        raise e
    except Exception as e:
        raise e


def _http_post(url: str, payload: dict, timeout: float = 60.0) -> bytes:
    """POST JSON, return full response bytes with safety timeouts."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "GravityAI/7.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _safe_json(raw: bytes | str) -> Optional[Dict[str, Any]]:
    if isinstance(raw, bytes):
        try:
            return json.loads(raw.decode("utf-8", errors="ignore"))
        except Exception:
            return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def _openai_compat_stream(
    base_url: str,
    path: str,
    payload: dict,
) -> Generator[str, None, None]:
    """
    Consumed by OpenAI-compatible local providers.
    Streams SSE lines and yields content string chunks.
    """
    url = f"{base_url.rstrip('/')}{path}"
    tool_calls_accumulator = {}
    try:
        for raw_line in _http_post_stream(url, payload):
            line = raw_line.decode("utf-8", errors="ignore").strip()
            if not line.startswith("data:"):
                continue
            data_str = line[5:].strip()
            if data_str == "[DONE]":
                break
            d = _safe_json(data_str)
            if d and "choices" in d and d["choices"]:
                delta = d["choices"][0].get("delta", {})
                
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
                
                chunk = delta.get("content", "")
                r_chunk = delta.get("reasoning_content", "")
                if r_chunk:
                    yield "<think>" + r_chunk + "</think>"
                if chunk:
                    yield chunk
                    
        if tool_calls_accumulator:
            tool_calls_list = [tool_calls_accumulator[i] for i in sorted(tool_calls_accumulator.keys())]
            yield json.dumps({"__TOOL_CALLS__": tool_calls_list})
            
    except Exception as e:
        yield f"\n\n[**SYSTEM ERROR**: Fallo de conexión con Modelo Local. Error: {str(e)}]\n\n"


def _openai_compat_complete(
    base_url: str,
    path: str,
    payload: dict,
) -> str:
    """Non-streaming for OpenAI-compatible endpoints."""
    try:
        url = f"{base_url.rstrip('/')}{path}"
        raw = _http_post(url, payload)
        data = _safe_json(raw)
        if data and "choices" in data and data["choices"]:
            msg = data["choices"][0].get("message", {})
            if "tool_calls" in msg:
                return json.dumps({"__TOOL_CALL__": msg["tool_calls"]})
            return msg.get("content", "")
    except Exception as e:
        import logging

        logging.getLogger("gravity").error(f"[BaseLocal] Error in completion: {e}")
    return ""


def _build_openai_payload(
    messages: List[Dict[str, Any]],
    model: str,
    options: Dict[str, Any],
    stream: bool,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"model": model, "messages": messages, "stream": stream}

    # Surgical parameter injection for LM Studio / OpenAI compatibility
    for k in ("temperature", "top_p", "tools", "tool_choice"):
        if k in options:
            payload[k] = options[k]

    if "max_tokens" in options and options["max_tokens"] > 0:
        payload["max_tokens"] = int(options["max_tokens"])

    # NEVER send empty stop list (causes 400 in many providers)
    if "stop" in options and options["stop"]:
        payload["stop"] = options["stop"]

    return payload
