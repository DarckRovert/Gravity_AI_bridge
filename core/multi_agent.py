"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         GRAVITY AI — MULTI-AGENT ORCHESTRATOR V7.2                           ║
║         Parallel, Sequential y Vote-based multi-model queries                ║
║         V7.2: Retrocompatibilidad Python 3.7+ (typing module)                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import time
import threading
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.provider_manager import get_plugin, get_all_model_names
import os

def _inject_master_plan(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Inyecta el Plan Maestro activo como contexto de sistema al inicio si existe."""
    try:
        from core.gravity_brain import _get_active_plan
        plan = _get_active_plan()
        if plan:
            # Comprobar si ya está inyectado
            for m in messages:
                if m.get("role") == "system" and "PLAN MAESTRO" in m.get("content", ""):
                    return messages
            new_msgs = list(messages)
            new_msgs.insert(0, {"role": "system", "content": plan})
            return new_msgs
    except Exception:
        pass
    return messages


# ── Parallel multi-model comparison ──────────────────────────────────────────

def compare(
    messages:  List[Dict[str, Any]],
    providers: Optional[List[str]]     = None,
    n_models:  int                     = 3,
    options:   Optional[Dict[str, Any]] = None,
    timeout:   float                   = 120.0,
) -> List[Dict[str, Any]]:
    """
    Sends the same messages to N providers/models in parallel.
    Returns list of {provider, model, response, elapsed}.
    providers: list of provider names. If None, picks top-N available.
    """
    options = options or {}
    messages = _inject_master_plan(messages)

    if not providers:
        all_models = get_all_model_names()
        providers  = list(all_models.keys())[:n_models]

    if not providers:
        return []

    results: List[Dict[str, Any]] = []
    lock = threading.Lock()

    def _query(provider_name: str) -> Dict[str, Any]:
        plugin = get_plugin(provider_name)
        if not plugin:
            return {
                "provider": provider_name,
                "model":    "N/A",
                "response": f"[{provider_name} not available]",
                "elapsed":  0,
            }
        health = plugin.check_health()
        if not health.is_healthy or not health.models:
            return {
                "provider": provider_name,
                "model":    "N/A",
                "response": f"[{provider_name} offline]",
                "elapsed":  0,
            }
        model = health.active_model or health.models[0]["name"]
        t0 = time.time()
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

    ex = ThreadPoolExecutor(max_workers=min(len(providers), 6))
    futures = {ex.submit(_query, p): p for p in providers}
    try:
        for future in as_completed(futures, timeout=timeout):
            try:
                results.append(future.result())
            except Exception:
                pass
    except TimeoutError:
        pass # Timeout alcanzado, retornamos los que hayan terminado
    finally:
        ex.shutdown(wait=False)

    return results


# ── Vote: majority consensus ──────────────────────────────────────────────────

def vote(
    messages:  List[Dict[str, Any]],
    providers: Optional[List[str]] = None,
    n_models:  int                 = 3,
    mode:      str                 = "vote",  # "vote" | "synthesize"
) -> Dict[str, Any]:
    """
    Runs parallel compare() and selects the best response.
    
    mode="vote"      → Selecciona la respuesta con mayor similitud semántica (TF-IDF cosine).
    mode="synthesize"→ Envía todas las respuestas a un modelo árbitro para sintetizar.
    """
    results = compare(messages, providers=providers, n_models=n_models)
    if not results:
        return {"provider": "N/A", "model": "N/A", "response": "[No results]", "elapsed": 0}
    if len(results) == 1:
        return results[0]

    if mode == "synthesize":
        from core.provider_manager import complete as pm_complete
        all_responses = "\n\n".join(
            f"[{r.get('provider')}/{r.get('model')}]:\n{r.get('response', '')[:1000]}"
            for r in results
        )
        synth_prompt = (
            "Eres un árbitro experto. Se te presentan las respuestas de varios modelos de IA a la misma pregunta. "
            "Sintetiza y unifica estas respuestas en una única respuesta final, coherente y completa, "
            "aprovechando los mejores elementos de cada una. No menciones qué modelo aportó qué.\n\n"
            f"PREGUNTA ORIGINAL:\n{messages[-1].get('content', '')[:500]}\n\n"
            f"RESPUESTAS:\n{all_responses}"
        )
        try:
            synth = pm_complete([{"role": "user", "content": synth_prompt}])
            if synth:
                return {"provider": "synthesized", "model": "multi", "response": synth, "elapsed": 0}
        except Exception:
            pass  # fallback a vote estándar

    # TF-IDF cosine similarity
    def _tfidf_vector(text: str) -> dict:
        import re
        from collections import Counter
        import math
        words = re.findall(r'\w+', text.lower())
        tf = Counter(words)
        total = sum(tf.values()) or 1
        return {w: c / total for w, c in tf.items()}

    def _cosine(v1: dict, v2: dict) -> float:
        common = set(v1) & set(v2)
        if not common:
            return 0.0
        dot = sum(v1[w] * v2[w] for w in common)
        norm1 = sum(x ** 2 for x in v1.values()) ** 0.5
        norm2 = sum(x ** 2 for x in v2.values()) ** 0.5
        return dot / (norm1 * norm2) if norm1 and norm2 else 0.0

    # Fallback a Jaccard para textos muy cortos (< 50 tokens)
    def _word_set(text: str) -> set:
        import re
        return set(re.findall(r'\w+', text.lower()))

    vectors = [_tfidf_vector(r["response"]) for r in results]
    use_cosine = all(len(r["response"].split()) >= 50 for r in results)

    best_score = -1.0
    best       = results[0]
    for i, r in enumerate(results):
        score = 0.0
        for j, other in enumerate(results):
            if i == j:
                continue
            if use_cosine:
                score += _cosine(vectors[i], vectors[j])
            else:
                ws_i = _word_set(r["response"])
                ws_j = _word_set(other["response"])
                inter = len(ws_i & ws_j)
                union = len(ws_i | ws_j) or 1
                score += inter / union
        score /= (len(results) - 1)
        if score > best_score:
            best_score = score
            best       = r

    method = "cosine" if use_cosine else "jaccard"
    return {**best, "vote_score": round(best_score, 3), "candidates": len(results), "method": method}



# ── Sequential pipeline ───────────────────────────────────────────────────────

class PipelineStep:
    """
    Representa un paso individual dentro de un pipeline de ejecución secuencial multi-modelo.
    """
    provider: str
    model: Optional[str]
    role: str

    def __init__(self, provider: str, model: Optional[str] = None, role: str = "") -> None:
        """
        Inicializa un paso del pipeline secuencial.

        Args:
            provider: Nombre del proveedor de IA para este paso.
            model: Nombre del modelo específico (opcional, usa el modelo activo si es None).
            role: Instrucción de rol o tarea asignada a este paso (ej. 'Refactoriza este código').
        """
        self.provider = provider
        self.model    = model
        self.role     = role


def run_pipeline(
    steps:            List[PipelineStep],
    initial_messages: List[Dict[str, Any]],
    options:          Optional[Dict[str, Any]] = None,
) -> str:
    """
    Ejecuta un pipeline secuencial de agentes multi-modelo en el que la salida
    de cada paso se convierte en la entrada del paso subsiguiente.
    """
    options  = options or {}
    history  = _inject_master_plan(list(initial_messages))
    last_out = ""

    for step in steps:
        plugin = get_plugin(step.provider)
        if not plugin:
            continue
        health = plugin.check_health()
        model  = step.model or (health.active_model if health.is_healthy else None)
        if not model:
            continue
        if step.role and last_out:
            history.append({"role": "user", "content": f"{step.role}:\n\n{last_out}"})
        chunks   = list(plugin.chat_stream(history, model, options))
        last_out = "".join(chunks)
        history.append({"role": "assistant", "content": last_out})

    return last_out
