"""
╔══════════════════════════════════════════════════════════════════════════════╗
║        GRAVITY AI - PROVIDER MANAGER V9.3 PRO [Diamond-Tier Edition]         ║
║                     Orquestador universal: local + cloud                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import time
import threading
from typing import Generator

from providers.registry import ProviderRegistry
from providers.base     import ProviderPlugin, ProviderResult

_lock              = threading.Lock()
_cached_results:   list[ProviderResult]  = []
_cached_plugins:   dict[str, ProviderPlugin] = {}  # name → plugin
_last_scan_time:   float = 0.0
_SCAN_TTL:         float = 30.0   # seconds before re-scanning


def _score_provider(result: ProviderResult, task: str) -> float:
    """
    Scores a provider result for routing.
    Higher = better. Task is "code" | "reason" | "any".
    """
    if not result.is_healthy:
        return -999.0

    score = 0.0

    # Category: local providers are preferred (0-latency after first load)
    if result.category == "local":
        score += 100.0
    else:
        score += 20.0

    # Model already loaded in GPU → big bonus
    if result.active_model:
        score += 50.0

    # Response time penalty
    score -= result.response_ms * 0.1

    # Task-specific model bonuses
    active = (result.active_model or "").lower()
    if task == "code":
        if any(k in active for k in ("coder", "codestral", "starcoder", "deepseek-coder")):
            score += 40.0
        if result.name in ("Groq",) and "qwen" in active:
            score += 30.0   # Groq + Qwen = fast code
    elif task == "reason":
        if any(k in active for k in ("r1", "reasoning", "qwq", "think")):
            score += 40.0
        if result.name in ("Anthropic",) and "claude" in active:
            score += 30.0   # Claude strong reasoner

    # Model parameter size bonus
    for size, bonus in [("70b", 25), ("72b", 25), ("32b", 20), ("26b", 18), ("14b", 10),
                        ("8b", 5), ("7b", 5)]:
        if size in active:
            score += bonus
            break

    return score


# ── Public API ─────────────────────────────────────────────────────────────────

def scan_all(force: bool = False) -> list[ProviderResult]:
    """
    Returns a list of ProviderResult for all known plugins.
    Results are cached for _SCAN_TTL seconds.
    """
    global _cached_results, _cached_plugins, _last_scan_time

    now = time.time()
    if not force and (now - _last_scan_time) < _SCAN_TTL and _cached_results:
        return _cached_results

    with _lock:
        now = time.time()
        if not force and (now - _last_scan_time) < _SCAN_TTL and _cached_results:
            return _cached_results

        results = ProviderRegistry.scan_all_health()
        plugins = {p.name: p for p in ProviderRegistry.get_all_plugins()}

        _cached_results  = results
        _cached_plugins  = plugins
        _last_scan_time  = time.time()

    return _cached_results


def get_best(task: str = "any") -> tuple[ProviderResult | None, str | None]:
    """
    Returns (ProviderResult, model_name) of the best provider for the task.
    Considers: local-first, active model in GPU, latency, task fit.
    Falls back to cloud if all local offline.
    """
    results = scan_all()
    healthy = [r for r in results if r.is_healthy and r.models]
    if not healthy:
        return None, None

    scored = sorted(healthy, key=lambda r: _score_provider(r, task), reverse=True)
    best   = scored[0]
    model  = best.active_model or best.models[0]["name"]
    return best, model


def get_plugin(name: str) -> ProviderPlugin | None:
    """Returns the ProviderPlugin instance for a given provider name."""
    scan_all()
    return _cached_plugins.get(name)


def get_active_plugin() -> ProviderPlugin | None:
    """Returns the plugin for the currently best provider."""
    result, _ = get_best()
    if result:
        return get_plugin(result.name)
    return None


def get_all_model_names() -> dict[str, list[str]]:
    """Returns {provider_name: [model_names]} for all healthy providers."""
    results = scan_all()
    out     = {}
    for r in results:
        if r.is_healthy and r.models:
            out[r.name] = [m["name"] for m in r.models]
    return out


def get_flat_model_list() -> list[str]:
    """Returns a flat deduplicated list of all available model names."""
    all_models = []
    seen       = set()
    for models in get_all_model_names().values():
        for m in models:
            if m not in seen:
                seen.add(m)
                all_models.append(m)
    return all_models


def stream(
    messages: list[dict],
    model:    str | None    = None,
    provider: str | None    = None,
    options:  dict | None   = None,
    task:     str           = "any",
) -> Generator[str, None, None]:
    """
    Universal streaming interface.
    Automatically routes to the best provider+model if not specified.
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
        yield "[ProviderManager] No provider available. Start Ollama or configure a cloud API key."
        return

    if not model:
        r = plugin.check_health()
        model = r.active_model or (r.models[0]["name"] if r.models else "unknown")

    yield from plugin.chat_stream(messages, model, options)


def complete(
    messages: list[dict],
    model:    str | None  = None,
    provider: str | None  = None,
    options:  dict | None = None,
    task:     str         = "any",
) -> str:
    """Universal non-streaming chat completion."""
    chunks = list(stream(messages, model, provider, options, task))
    return "".join(chunks)


def get_cost_estimate(provider_name: str, model: str, input_chars: int, output_chars: int = 0) -> float:
    """Estimates cost in USD for a request."""
    plugin = get_plugin(provider_name)
    if not plugin:
        return 0.0
    costs  = plugin.get_cost_per_million_tokens(model)
    input_tokens  = input_chars  / 4.0   # rough estimate
    output_tokens = output_chars / 4.0
    return (input_tokens * costs["input"] + output_tokens * costs["output"]) / 1_000_000


if __name__ == "__main__":
    print("Provider Manager V9.3 — Universal scan\n")
    results = scan_all(force=True)
    for r in results:
        tag = "✅" if r.is_healthy else "🔴"
        key = "🔑" if r.key_configured else ("🌐" if r.category == "cloud" else "")
        print(f"  {tag} {key}  {r.name:<20} {r.url:<45} {r.model_count}M  {r.response_ms}ms")

    best_r, best_m = get_best()
    if best_r:
        print(f"\n  Best: {best_r.name} / {best_m}")
