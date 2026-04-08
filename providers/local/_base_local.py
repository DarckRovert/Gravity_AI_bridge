"""
providers/local/_base_local.py — Shared HTTP helper for local providers V7.1
Internal — not auto-discovered by registry (filename starts with _).
"""

import json
import time
import socket
import urllib.request
import urllib.error
from typing import Generator


def _http_get(url: str, timeout: float = 1.0) -> dict | None:
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
    "embed", "embedding", "rerank", "reranker", "classifier",
    "moderation", "nomic-embed", "text-embedding", "bge-",
    "e5-", "gte-", "instructor-", "sentence-", "all-minilm",
    "clip", "whisper", "tts", "vision-encoder",
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


def filter_chat_models(models: list[dict]) -> list[dict]:
    """
    Filtra una lista de {name, size} devolviendo solo los modelos aptos para chat.
    Si NINGUNO es apto (situación improbable), devuelve la lista original completa
    para no dejar el provider sin modelos.
    """
    chat_only = [m for m in models if is_chat_model(m.get("name", ""))]
    return chat_only if chat_only else models


def pick_active_model(models: list[dict]) -> str | None:
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
    timeout: float = 1800,
) -> Generator[bytes, None, None]:
    """POST JSON, yield raw response lines."""
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json", "User-Agent": "GravityAI/7.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            for line in r:
                yield line
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="ignore")
        yield f"[Gravity Error] HTTP {e.code}: {error_body}".encode("utf-8")
    except Exception as e:
        yield f"[Gravity Error] {str(e)}".encode("utf-8")


def _http_post(url: str, payload: dict, timeout: float = 1800) -> bytes:
    """POST JSON, return full response bytes."""
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json", "User-Agent": "GravityAI/7.0"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _safe_json(raw: bytes | str) -> dict | None:
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
            chunk = delta.get("content", "")
            r_chunk = delta.get("reasoning_content", "")
            if r_chunk:
                # Usar <think> en lugar de ANSI: los codigos ANSI se muestran
                # como texto crudo en HTML. ReasoningStripper los elimina en
                # bridge_server (web) y en ask_deepseek (CLI).
                yield "<think>" + r_chunk + "</think>"
            if chunk:
                yield chunk


def _openai_compat_complete(
    base_url: str,
    path: str,
    payload: dict,
) -> str:
    """Non-streaming for OpenAI-compatible endpoints."""
    url  = f"{base_url.rstrip('/')}{path}"
    raw  = _http_post(url, payload)
    data = _safe_json(raw)
    if data and "choices" in data and data["choices"]:
        return data["choices"][0].get("message", {}).get("content", "")
    return ""


def _build_openai_payload(
    messages: list[dict],
    model:    str,
    options:  dict,
    stream:   bool,
) -> dict:
    payload: dict = {"model": model, "messages": messages, "stream": stream}
    
    # Surgical parameter injection for LM Studio / OpenAI compatibility
    if "temperature" in options:
        payload["temperature"] = float(options["temperature"])
    if "top_p" in options:
        payload["top_p"] = float(options["top_p"])
    if "max_tokens" in options and options["max_tokens"] > 0:
        payload["max_tokens"] = int(options["max_tokens"])
    
    # NEVER send empty stop list (causes 400 in many providers)
    if "stop" in options and options["stop"]:
        payload["stop"] = options["stop"]
        
    return payload
