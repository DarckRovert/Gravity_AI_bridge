"""
╔══════════════════════════════════════════════════════════════╗
║     GRAVITY AI — MULTI-AGENT ORCHESTRATOR V7.1               ║
║     Parallel, Sequential y Vote-based multi-model queries    ║
╚══════════════════════════════════════════════════════════════╝
"""
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.provider_manager import get_plugin, get_all_model_names


# ── Parallel multi-model comparison ──────────────────────────────────────────

def compare(
    messages:  list[dict],
    providers: list[str] | None   = None,
    n_models:  int                = 3,
    options:   dict | None        = None,
    timeout:   float              = 120.0,
) -> list[dict]:
    """
    Sends the same messages to N providers/models in parallel.
    Returns list of {"provider": str, "model": str, "response": str, "elapsed": float}.
    providers: list of provider names to use. If None, picks top-N available.
    """
    options = options or {}

    # Auto-select providers if not specified
    if not providers:
        all_models = get_all_model_names()
        providers  = list(all_models.keys())[:n_models]

    results  = []
    lock     = threading.Lock()

    def _query(provider_name: str) -> dict:
        plugin = get_plugin(provider_name)
        if not plugin:
            return {"provider": provider_name, "model": "N/A", "response": f"[{provider_name} not available]", "elapsed": 0}
        health = plugin.check_health()
        if not health.is_healthy or not health.models:
            return {"provider": provider_name, "model": "N/A", "response": f"[{provider_name} offline]", "elapsed": 0}
        model = health.active_model or health.models[0]["name"]
        t0    = time.time()
        try:
            chunks   = list(plugin.chat_stream(messages, model, options))
            response = "".join(chunks)
        except Exception as e:
            response = f"[Error: {e}]"
        return {
            "provider": provider_name,
            "model":    model,
            "response": response,
            "elapsed":  round(time.time() - t0, 2),
        }

    with ThreadPoolExecutor(max_workers=min(len(providers), 6)) as ex:
        futures = {ex.submit(_query, p): p for p in providers}
        for future in as_completed(futures, timeout=timeout):
            try:
                results.append(future.result())
            except Exception:
                pass

    return results


# ── Vote: majority consensus ──────────────────────────────────────────────────

def vote(
    messages:  list[dict],
    providers: list[str] | None = None,
    n_models:  int              = 3,
) -> dict:
    """
    Runs parallel compare() and selects the response with least divergence
    (centroid similarity via word overlap — no embeddings required).
    Returns the winning response dict.
    """
    results = compare(messages, providers=providers, n_models=n_models)
    if not results:
        return {"provider": "N/A", "model": "N/A", "response": "[No results]", "elapsed": 0}
    if len(results) == 1:
        return results[0]

    def _word_set(text: str) -> set:
        import re
        return set(re.findall(r'\w+', text.lower()))

    # Score each result by average Jaccard similarity to all others
    best_score = -1.0
    best       = results[0]
    for i, r in enumerate(results):
        ws_i  = _word_set(r["response"])
        score = 0.0
        for j, other in enumerate(results):
            if i == j:
                continue
            ws_j  = _word_set(other["response"])
            inter = len(ws_i & ws_j)
            union = len(ws_i | ws_j) or 1
            score += inter / union
        score /= (len(results) - 1)
        if score > best_score:
            best_score = score
            best       = r

    return {**best, "vote_score": round(best_score, 3), "candidates": len(results)}


# ── Sequential pipeline ───────────────────────────────────────────────────────

class PipelineStep:
    def __init__(self, provider: str, model: str = None, role: str = ""):
        self.provider = provider
        self.model    = model
        self.role     = role   # e.g. "Refactor this code", "Review and find bugs"


def run_pipeline(steps: list[PipelineStep], initial_messages: list[dict], options: dict = None) -> str:
    """
    Runs a sequential pipeline where each step's output becomes the next step's input.
    The output of each step is appended as a new user message for the next step.
    """
    options  = options or {}
    history  = list(initial_messages)
    last_out = ""

    for step in steps:
        plugin = get_plugin(step.provider)
        if not plugin:
            continue
        health = plugin.check_health()
        model  = step.model or (health.active_model if health.is_healthy else None)
        if not model:
            continue
        # Inject the step's role prompt if specified
        if step.role and last_out:
            history.append({"role": "user", "content": f"{step.role}:\n\n{last_out}"})
        chunks   = list(plugin.chat_stream(history, model, options))
        last_out = "".join(chunks)
        history.append({"role": "assistant", "content": last_out})

    return last_out
