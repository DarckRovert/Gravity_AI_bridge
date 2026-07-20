"""
╔══════════════════════════════════════════════════════════════════════════════╗
║      GRAVITY AI - PROVIDER MANAGER V17.0 PRO [Swarm Edition]                ║
║      Orquestador universal: local + cloud + enjambre round-robin            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import time
import threading
import json as _j
import os as _os
from typing import Generator, List, Dict, Tuple, Optional, Any

from providers.registry import ProviderRegistry
from providers.base import ProviderPlugin, ProviderResult, ProviderResponse

_lock = threading.RLock()
_cached_results: List[ProviderResult] = []
_cached_plugins: Dict[str, ProviderPlugin] = {}  # name → plugin
_last_scan_time: float = 0.0
_SCAN_TTL: float = 180.0  # segundos antes de re-escanear

# ── Enjambre (Swarm) Round-Robin ─────────────────────────────────────────────
# Cada llamada al LLM recibe el siguiente proveedor saludable en la lista.
# Thread-safe. No bloquea llamadas paralelas entre proveedores distintos.
_swarm_counter: int = 0
_swarm_lock = threading.Lock()

# Lock por proveedor individual — permite paralelismo entre proveedores distintos
# pero serializa las llamadas al mismo proveedor (evita race conditions).
_provider_locks: Dict[str, threading.Lock] = {}
_provider_locks_lock = threading.Lock()
_INFERENCE_LOCK_TIMEOUT: float = 180.0

# Alias de compatibilidad: el lock global ya no bloquea en modo swarm,
# pero lo mantenemos para que imports externos no fallen.
_inference_lock = threading.Lock()


def _get_provider_lock(provider_name: str) -> threading.Lock:
    """Returns (or creates) a per-provider lock. Thread-safe."""
    with _provider_locks_lock:
        if provider_name not in _provider_locks:
            _provider_locks[provider_name] = threading.Lock()
        return _provider_locks[provider_name]


def _load_settings() -> Dict[str, Any]:
    """Reads settings from _settings.json thread-safely."""
    with _lock:
        try:
            _base = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
            settings_path = _os.path.join(_base, "_settings.json")
            if not _os.path.exists(settings_path):
                return {}
            with open(settings_path, "r", encoding="utf-8") as _f:
                data = _j.load(_f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}


def _score_model(result: ProviderResult, model_name: str, task: str) -> float:
    """
    Scores a specific model from a provider result for routing.
    Higher = better.
    """
    if not result.is_healthy:
        return -999.0

    score = 0.0

    # Category: local providers are preferred (0-latency after first load)
    if result.category == "local":
        score += 100.0
    else:
        score += 20.0

    # ── NPU Priority Boost ────────────────────────────────────────────────────
    # FastFlowLM corre en la NPU AMD XDNA (Ryzen AI). Cuando está activo y saludable,
    # debe tener prioridad absoluta: deja libre la GPU/CPU para el resto del sistema.
    if result.name == "FastFlowLM (NPU)" and result.is_healthy:
        score += 200.0  # Supera cualquier proveedor local por CPU/GPU

    # Model already loaded in GPU → big bonus
    if result.active_model == model_name:
        score += 50.0

    # Response time penalty (FLM durante carga inicial puede tener latencia alta, no penalizar exageradamente)
    if result.name == "FastFlowLM (NPU)":
        score -= min(result.response_ms * 0.05, 100.0)  # cap 100 pts de penalización
    else:
        score -= result.response_ms * 0.1

    # Task-specific model bonuses
    active = model_name.lower()

    if task == "vision":
        if "llava" in active:
            score += 150.0
    elif task == "embedding":
        if "nomic" in active:
            score += 150.0
    elif task == "code":
        if "qwen" in active and "coder" in active:
            score += 80.0
        elif any(
            k in active for k in ("coder", "codestral", "starcoder", "deepseek-coder")
        ):
            score += 40.0
        if result.name in ("Groq",) and "qwen" in active:
            score += 30.0
    elif task == "reason":
        if "hermes" in active:
            score += 70.0
        if any(k in active for k in ("r1", "reasoning", "qwq", "think")):
            score += 50.0
        if result.name in ("Anthropic",) and "claude" in active:
            score += 30.0
    elif task == "bounty":
        if "qwen" in active and "coder" in active:
            score += 70.0
        elif any(k in active for k in ("qwen", "coder", "phi")):
            score += 40.0
        if "nemo" in active or "70b" in active:
            score -= 20.0
    elif task == "semantic":
        if "hermes" in active:
            score += 70.0
        elif any(k in active for k in ("hermes", "nemo", "llama-3")):
            score += 40.0
        if "coder" in active or "phi" in active:
            score -= 30.0

    # Penalizaciones para evitar malas rutas
    if task != "embedding" and "nomic" in active:
        score -= 250.0  # nomic no es para chat
    if task != "vision" and "llava" in active:
        score -= (
            60.0  # llava es para vision, no para chat estandar si hay mejores opciones
        )

    # Model parameter size bonus
    for size, bonus in [
        ("70b", 25),
        ("72b", 25),
        ("32b", 20),
        ("26b", 18),
        ("14b", 10),
        ("8b", 5),
        ("7b", 5),
    ]:
        if size in active:
            score += bonus
            break

    return score


# ── Public API ─────────────────────────────────────────────────────────────────



def scan_all(force: bool = False) -> List[ProviderResult]:
    """
    Returns a list of ProviderResult for all known plugins.
    Results are cached for _SCAN_TTL seconds.
    Health checks run in parallel with 8s timeout per provider to prevent stalls.
    """
    global _cached_results, _cached_plugins, _last_scan_time
    import concurrent.futures

    now = time.time()
    if not force and (now - _last_scan_time) < _SCAN_TTL and _cached_results:
        return _cached_results

    with _lock:
        now = time.time()
        if not force and (now - _last_scan_time) < _SCAN_TTL and _cached_results:
            return _cached_results

        plugins = ProviderRegistry.get_all_plugins()

        def _safe_check(plugin: ProviderPlugin) -> ProviderResult:
            try:
                return plugin.check_health()
            except Exception as _e:
                r = ProviderResult(
                    name=plugin.name,
                    url=getattr(plugin, "base_url", ""),
                    protocol=getattr(plugin, "protocol", "unknown"),
                    category=getattr(plugin, "category", "local"),
                )
                r.is_healthy = False
                r.models = []
                r.active_model = None
                r.response_ms = 0
                r.key_configured = False
                return r

        results: List[ProviderResult] = []
        try:
            ex = concurrent.futures.ThreadPoolExecutor(
                max_workers=min(len(plugins), 8), thread_name_prefix="GravityScan"
            )
            futures = {ex.submit(_safe_check, p): p for p in plugins}
            
            end_time = time.time() + 8.0  # 8 segundos de timeout global
            for fut, plug in futures.items():
                remaining = end_time - time.time()
                if remaining <= 0:
                    remaining = 0.001
                try:
                    res = fut.result(timeout=remaining)
                    results.append(res)
                except concurrent.futures.TimeoutError:
                    # Si hay un timeout por swapping o lentitud, intentamos usar el estado anterior
                    cached_r = next((r for r in _cached_results if r.name == plug.name), None)
                    if cached_r:
                        results.append(cached_r)
                    else:
                        r = ProviderResult(
                            name=plug.name,
                            url=getattr(plug, "base_url", ""),
                            protocol=getattr(plug, "protocol", "unknown"),
                            category=getattr(plug, "category", "local"),
                        )
                        r.is_healthy = False
                        r.models = []
                        r.active_model = None
                        r.response_ms = 20000
                        r.key_configured = False
                        results.append(r)
                except Exception:
                    pass
        except RuntimeError as e:
            from core.logger import log
            log.warning(f"[ProviderManager] ThreadPoolExecutor falló ({e}). Usando escaneo secuencial (Fallback).")
            # Fallback secuencial si no se pueden crear hilos (ej. memoria agotada o interpreter shutdown)
            for p in plugins:
                try:
                    results.append(_safe_check(p))
                except Exception:
                    pass
        finally:
            if 'ex' in locals():
                ex.shutdown(wait=False)

        _cached_results = results
        _cached_plugins = {p.name: p for p in plugins}
        _last_scan_time = time.time()

    return _cached_results


def get_best(task: str = "any") -> Tuple[Optional[ProviderResult], Optional[str]]:
    """
    Returns (ProviderResult, model_name) of the best provider for the task.
    Local-first. If all local providers are offline, promotes cloud.
    If all providers are unhealthy, returns (None, None) — never raises.
    """
    # Si hay bloqueo global de modelo activo, lo honramos inmediatamente
    try:
        _settings = _load_settings()
        if _settings.get("model_locked", False):
            locked_p = _settings.get("locked_provider")
            locked_m = _settings.get("locked_model")
            if locked_p and locked_m:
                for r in scan_all():
                    if r.name == locked_p:
                        return r, locked_m
    except Exception:
        pass

    results = scan_all()
    healthy = [r for r in results if r.is_healthy and r.models]
    if not healthy:
        return None, None

    # Separate local vs cloud to enforce local-first
    local_healthy = [r for r in healthy if r.category == "local"]
    cloud_healthy = [r for r in healthy if r.category != "local"]

    candidates = local_healthy if local_healthy else cloud_healthy

    best_score = -9999.0
    best_pair = (candidates[0], candidates[0].models[0]["name"])

    for r in candidates:
        for m in r.models:
            m_name = m["name"]
            score = _score_model(r, m_name, task)
            if score > best_score:
                best_score = score
                best_pair = (r, m_name)

    return best_pair


def get_ranked_providers(task: str = "any") -> List[Tuple[ProviderResult, str]]:
    """
    Returns ALL healthy (provider, model) pairs sorted by score descending.
    Used by swarm routing to pick the Nth best provider.
    Enjambre Híbrido: Mezcla Local y Nube al mismo tiempo.
    """
    results = scan_all()
    healthy = [r for r in results if r.is_healthy and r.models]
    if not healthy:
        return []

    # En el enjambre, queremos TODOS los candidatos (Local + Cloud) para distribuirlos
    candidates = healthy

    scored: List[Tuple[float, ProviderResult, str]] = []
    for r in candidates:
        for m in r.models:
            m_name = m["name"]
            score = _score_model(r, m_name, task)
            scored.append((score, r, m_name))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [(r, m) for _, r, m in scored]


def get_swarm_provider(task: str = "any") -> Tuple[Optional[ProviderResult], Optional[str]]:
    """
    Enjambre Round-Robin: cada llamada devuelve el siguiente proveedor saludable
    en orden rotativo. Permite que múltiples nodos usen distintas IAs en paralelo.
    Cae de vuelta a get_best() si solo hay 1 proveedor disponible.
    """
    global _swarm_counter
    ranked = get_ranked_providers(task)
    if not ranked:
        return None, None
    if len(ranked) == 1:
        return ranked[0]
    with _swarm_lock:
        idx = _swarm_counter % len(ranked)
        _swarm_counter += 1
    return ranked[idx]


def _get_provider_lock(provider_name: str) -> threading.Lock:
    """Returns (creating if needed) the per-provider lock."""
    with _provider_locks_lock:
        if provider_name not in _provider_locks:
            _provider_locks[provider_name] = threading.Lock()
        return _provider_locks[provider_name]


def get_plugin(name: str) -> Optional[ProviderPlugin]:
    """Returns the ProviderPlugin instance for a given provider name."""
    scan_all()
    with _lock:
        return _cached_plugins.get(name)


def get_active_plugin() -> Optional[ProviderPlugin]:
    """Returns the plugin for the currently best provider."""
    result, _ = get_best()
    if result:
        return get_plugin(result.name)
    return None


def get_all_model_names() -> Dict[str, List[str]]:
    """Returns {provider_name: [model_names]} for all healthy providers."""
    results = scan_all()
    out: Dict[str, List[str]] = {}
    for r in results:
        if r.is_healthy and r.models:
            out[r.name] = [m["name"] for m in r.models]
    return out


def get_flat_model_list() -> List[str]:
    """Returns a flat deduplicated list of all available model names."""
    all_models: List[str] = []
    seen = set()
    for models in get_all_model_names().values():
        for m in models:
            if m not in seen:
                seen.add(m)
                all_models.append(m)
    return all_models


def stream(
    messages: List[Dict[str, Any]],
    model: Optional[str] = None,
    provider: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
    task: str = "any",
    _visited_providers: Optional[set] = None,
) -> Generator[str, None, None]:
    """
    Universal streaming interface.
    Automatically routes to the best provider+model if not specified.
    """
    options = options or {}

    # Honor global model lock from _settings.json if not explicitly overridden by calling function
    if not provider and not model:
        try:
            _settings = _load_settings()
            if _settings.get("model_locked", False):
                locked_p = _settings.get("locked_provider")
                locked_m = _settings.get("locked_model")
                if locked_p and locked_m:
                    provider = locked_p
                    model = locked_m
        except Exception:
            pass

    if provider:
        plugin = get_plugin(provider)
    else:
        result, auto_model = get_best(task)
        plugin = get_plugin(result.name) if result else None
        if not model:
            model = auto_model

    if not plugin:
        yield "[ProviderManager] No provider available. Start Ollama or configure a cloud API key."
        return

    if not model:
        r = plugin.check_health()
        model = r.active_model or (r.models[0]["name"] if r.models else "unknown")

    _visited = _visited_providers or set()
    if plugin.name in _visited:
        raise Exception(f"Bucle de Fallback detectado. Todos los motores de respaldo fallaron.")
    _visited.add(plugin.name)

    # Serializar acceso por proveedor — permite paralelismo entre distintos motores en Enjambre
    prov_lock = _get_provider_lock(plugin.name)
    acquired = prov_lock.acquire(timeout=_INFERENCE_LOCK_TIMEOUT)
    if not acquired:
        raise Exception(f"[ProviderManager] Proveedor {plugin.name} ocupado procesando otra tarea (ingesta pesada de tokens/TTFT). Reintenta en un par de minutos.")
    lock_released = False
    try:
        stream_committed = False  # True tras el primer chunk emitido al cliente
        chunks_yielded = 0        # Contador de chunks — usado en el fallback
        try:
            for chunk in plugin.chat_stream(messages, model, options):
                stream_committed = True
                chunks_yielded += 1
                yield chunk
            if chunks_yielded == 0:
                raise Exception("Empty response (Timeout o error de conexión)")
        except Exception as e:
            from core.logger import log
            log.warning(f"[ProviderManager] Proveedor principal '{plugin.name}' falló: {e}. Activando Fallback...")

            # Patrón monotónico (Vocero): si ya emitimos datos al cliente,
            # NO mezclar con respuesta de otro proveedor. El stream está comprometido.
            if stream_committed:
                log.warning("[ProviderManager] Stream comprometido (ya se emitieron chunks). Fallback omitido para evitar corrupción.")
                return

            # Buscar el proveedor de respaldo, excluyendo obligatoriamente a los que ya fallaron
            ranked = get_ranked_providers(task)
            fallback_res, fallback_mod = None, None
            for r, m in ranked:
                if r.name not in _visited:
                    fallback_res, fallback_mod = r, m
                    break

            if fallback_res:
                fallback_plug = get_plugin(fallback_res.name)
                if fallback_plug:
                    log.info(f"[ProviderManager] Fallback activado -> Usando {fallback_plug.name} ({fallback_mod})")
                    # Soltamos el lock del proveedor original para evitar dead-locks
                    prov_lock.release()
                    lock_released = True
                    # Recursión para re-iniciar el stream adquiriendo correctamente el lock del Fallback
                    yield from stream(messages, fallback_mod, fallback_plug.name, options, task, _visited)
                    return
                else:
                    if chunks_yielded == 0:
                        raise Exception("Fallo proveedor principal y motor de respaldo no encontrado.")
            else:
                if chunks_yielded == 0:
                    raise Exception("Fallo proveedor principal y es el único motor configurado/saludable.")
    finally:
        if not lock_released:
            prov_lock.release()


def complete(
    messages: List[Dict[str, Any]],
    model: Optional[str] = None,
    provider: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
    task: str = "any",
) -> str:
    """Universal non-streaming chat completion."""
    chunks = list(stream(messages, model, provider, options, task))
    return "".join(chunks)


def complete_safe(
    messages: List[Dict[str, Any]],
    model: Optional[str] = None,
    provider: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
    task: str = "any",
) -> ProviderResponse:
    """
    Universal non-streaming chat con resultado discriminado (Vocero-pattern).
    NUNCA lanza excepción al caller. Retorna ProviderResponse(ok=False, error=...) en fallo.
    """
    options = options or {}

    if provider:
        plugin = get_plugin(provider)
    else:
        result, auto_model = get_best(task)
        plugin = get_plugin(result.name) if result else None
        if not model:
            model = auto_model

    if not plugin:
        return ProviderResponse(
            ok=False, error="network",
            detail="No hay proveedores disponibles. Inicia Ollama o configura una API key."
        )

    if not model:
        r = plugin.check_health()
        model = r.active_model or (r.models[0]["name"] if r.models else "unknown")

    return plugin.chat_complete_safe(messages, model, options)


def complete_json(
    messages: List[Dict[str, Any]],
    model: Optional[str] = None,
    provider: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
    task: str = "any",
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Extrae JSON válido de la respuesta del LLM con 3 estrategias de fallback
    y hasta max_retries reintentos (Vocero chatJson pattern).

    Retorna:
      {"ok": True,  "data": {...}}            → JSON extraído correctamente
      {"ok": False, "error": str, "raw": str} → no se pudo extraer JSON válido
    """
    import re
    import json as _json

    def _try_extract(text: str) -> Optional[Dict]:
        """3 estrategias de extracción en orden de especificidad."""
        # 1. Bloque ```json ... ```
        m = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
        if m:
            try:
                return _json.loads(m.group(1))
            except Exception:
                pass

        # 2. Texto completo (el modelo respondió JSON puro)
        try:
            return _json.loads(text.strip())
        except Exception:
            pass

        # 3. Primer objeto balanceado {...}
        depth = 0
        start = -1
        for i, ch in enumerate(text):
            if ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and start != -1:
                    try:
                        return _json.loads(text[start:i + 1])
                    except Exception:
                        start = -1  # sigue buscando el siguiente objeto
        return None

    current_messages = list(messages)
    last_raw = ""

    for attempt in range(max_retries):
        resp = complete_safe(current_messages, model, provider, options, task)
        if not resp.ok:
            return {"ok": False, "error": f"{resp.error}: {resp.detail}", "raw": ""}

        last_raw = resp.text
        extracted = _try_extract(last_raw)
        if extracted is not None:
            return {"ok": True, "data": extracted}

        # Reintento: agregar mensaje de corrección (Vocero pattern)
        if attempt < max_retries - 1:
            current_messages = list(messages) + [
                {"role": "assistant", "content": last_raw},
                {
                    "role": "user",
                    "content": (
                        "Tu respuesta anterior no era JSON válido. "
                        "Responde SOLAMENTE con un objeto JSON válido, sin texto adicional, "
                        "sin bloques de código markdown."
                    )
                }
            ]

    from core.logger import log
    log.warning(f"[ProviderManager] complete_json() falló tras {max_retries} intentos. Última respuesta: {last_raw[:200]}")
    return {"ok": False, "error": "invalid_response", "raw": last_raw}


def complete_structured(
    schema: Any,
    messages: List[Dict[str, Any]],
    model: Optional[str] = None,
    provider: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
    task: str = "any",
    max_retries: int = 3,
) -> Any:
    """
    Envoltura Pydantic que usa core.llm_frontier.chat_structured
    para garantizar la validación de un esquema.
    Retorna un ChatResult[T].
    """
    from core.llm_frontier import chat_structured
    
    def _completer(msgs: List[Dict[str, Any]], **kwargs) -> str:
        res = complete_safe(msgs, model, provider, options, task)
        return res.text if res.ok else ""
        
    return chat_structured(
        schema=schema,
        complete_fn=_completer,
        messages=messages,
        max_attempts=max_retries
    )


def get_cost_estimate(
    provider_name: str, model: str, input_chars: int, output_chars: int = 0
) -> float:
    """Estimates cost in USD for a request."""
    plugin = get_plugin(provider_name)
    if not plugin:
        return 0.0
    costs = plugin.get_cost_per_million_tokens(model)
    input_tokens = input_chars / 4.0  # rough estimate
    output_tokens = output_chars / 4.0
    return (input_tokens * costs["input"] + output_tokens * costs["output"]) / 1_000_000


if __name__ == "__main__":
    print("Provider Manager V16.0 PRO — Universal scan\n")
    results = scan_all(force=True)
    for r in results:
        tag = "✅" if r.is_healthy else "🔴"
        key = "🔑" if r.key_configured else ("🌐" if r.category == "cloud" else "")
        print(
            f"  {tag} {key}  {r.name:<20} {r.url:<45} {r.model_count}M  {r.response_ms}ms"
        )

    best_r, best_m = get_best()
    if best_r:
        print(f"\n  Best: {best_r.name} / {best_m}")
