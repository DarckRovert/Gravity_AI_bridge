"""
╔══════════════════════════════════════════════════════════════════════════════╗
║        GRAVITY AI - PROVIDER MANAGER V16.0 PRO [Diamond-Tier Edition]         ║
║                     Orquestador universal: local + cloud                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import time
import threading
import json as _j
import os as _os
from typing import Generator, List, Dict, Tuple, Optional, Any

from providers.registry import ProviderRegistry
from providers.base import ProviderPlugin, ProviderResult

_lock = threading.RLock()
_cached_results: List[ProviderResult] = []
_cached_plugins: Dict[str, ProviderPlugin] = {}  # name → plugin
_last_scan_time: float = 0.0
_SCAN_TTL: float = 180.0  # segundos antes de re-escanear (B2: 3 min — reduce overhead en workflows largos)

# Lock global de inferencia — serializa todas las llamadas al LLM.
# Evita condición de carrera entre daemons de fondo y el chat del usuario.
# Timeout de 120s para que ninguna llamada quede bloqueada para siempre.
_inference_lock = threading.Lock()
_INFERENCE_LOCK_TIMEOUT: float = 120.0


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
    # FastFlowLM corre en la NPU AMD XDNA (Ryzen AI). Cuando está activo,
    # debe tener prioridad absoluta: deja libre la GPU/CPU para el resto del sistema.
    if result.name == "FastFlowLM (NPU)":
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

    # Serializar acceso al LLM — evita condiciones de carrera entre daemons y el chat
    acquired = _inference_lock.acquire(timeout=_INFERENCE_LOCK_TIMEOUT)
    if not acquired:
        yield "[ProviderManager] Motor de IA ocupado. Reintenta en unos segundos."
        return
    try:
        chunks_yielded = 0
        try:
            for chunk in plugin.chat_stream(messages, model, options):
                chunks_yielded += 1
                yield chunk
            if chunks_yielded == 0:
                raise Exception("Empty response (Timeout o error de conexión)")
        except Exception as e:
            from core.logger import log
            log.warning(f"[ProviderManager] Proveedor principal '{plugin.name}' falló: {e}. Activando Fallback...")
            
            # Buscar el segundo mejor proveedor
            fallback_res, fallback_mod = get_best(task)
            if fallback_res and fallback_res.name != plugin.name:
                fallback_plug = get_plugin(fallback_res.name)
                if fallback_plug:
                    log.info(f"[ProviderManager] Fallback activado -> Usando {fallback_plug.name} ({fallback_mod})")
                    yield from fallback_plug.chat_stream(messages, fallback_mod, options)
                else:
                    if chunks_yielded == 0:
                        raise Exception("Fallo proveedor principal y no hay motores de respaldo.")
            else:
                if chunks_yielded == 0:
                    raise Exception("Fallo proveedor principal y es el único motor configurado/saludable.")
    finally:
        _inference_lock.release()


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
