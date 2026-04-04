"""
╔══════════════════════════════════════════════════════════╗
║     GRAVITY AI SMART MODEL SELECTOR V5.1                 ║
║     Selección Inteligente de Modelo por Tarea            ║
╚══════════════════════════════════════════════════════════╝

Decisión automática del modelo óptimo según el tipo de tarea.
NUNCA usa dos modelos simultáneamente — uno carga, el otro espera.

Lógica de selección:
  🔵 Código / Auditoría / Bug   → Qwen2.5-Coder (especialista en código)
  🟠 Razonamiento / Análisis    → DeepSeek-R1 (piensa antes de responder)
  ⚪ General / Conversación     → El modelo más rápido disponible

Compatible con: Ollama, Lemonade, LM Studio, KoboldCPP, Jan AI
"""

import json
import os
import urllib.request
import urllib.error
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Perfiles de tarea con pesos por palabra clave ──────────────────────────────
TASK_PROFILES = {
    "code": {
        "weight": 0,
        "keywords": {
            # Commands that inject files are always code tasks
            "/leer": 5, "/leer-carpeta": 5, "/leer-git": 4,
            # Code-specific Spanish/English terms
            "código": 3, "code": 3, "bug": 4, "error": 2,
            "función": 3, "function": 3, "clase": 3, "class": 3,
            "script": 3, "refactor": 4, "optimiza": 3, "optimize": 3,
            "audita": 4, "audit": 4, "implementa": 3, "implement": 3,
            "python": 3, "rust": 3, "javascript": 3, "typescript": 3,
            "golang": 3, "java": 3, "c++": 3, "kotlin": 3,
            ".py": 4, ".rs": 4, ".js": 3, ".ts": 3, ".go": 3,
            "def ": 3, "return ": 2, "import ": 2, "class ": 3,
            "async": 2, "await": 2, "const ": 2, "let ": 2, "var ": 2,
            "test": 2, "unittest": 3, "pytest": 3, "debug": 3,
            "api": 2, "endpoint": 2, "request": 2, "response": 2,
            "sql": 3, "query": 2, "database": 2, "schema": 2,
            "```": 3,  # Code blocks = definitely a code task
        },
        "preferred_model_keywords": ["coder", "code", "starcoder", "codellama", "deepseek-coder"],
        "description": "Code generation, audit, debugging, refactoring",
        "switch_message": "[CODE] Switching to code specialist model..."
    },
    "reason": {
        "weight": 0,
        "keywords": {
            # Deep thinking Spanish terms
            "por qué": 3, "porque": 2, "razona": 4, "razonamiento": 4,
            "explica": 2, "como funciona": 3, "cómo funciona": 3,
            "analiza": 3, "analyze": 3, "comprende": 2, "understand": 2,
            "planifica": 3, "plan": 2, "estrategia": 3, "strategy": 3,
            "arquitectura": 3, "architecture": 3, "diseña": 2, "design": 2,
            "compara": 3, "compare": 3, "diferencia": 2, "difference": 2,
            "ventajas": 2, "desventajas": 2, "pros": 2, "cons": 2,
            "decide": 3, "debería": 2, "should": 2, "mejor opción": 3,
            "investiga": 3, "research": 3, "aprende": 2, "learn": 2,
            "matemática": 4, "math": 4, "álgebra": 4, "cálculo": 4,
            "lógica": 3, "logic": 3, "demostrar": 3, "prove": 3,
            "qué es": 2, "what is": 2, "explica cómo": 3,
            "brainstorm": 4, "ideas": 2, "creatividad": 3, "creative": 3,
            "think": 3, "piensa": 3, "reflexiona": 4, "recomienda": 3,
        },
        "preferred_model_keywords": ["deepseek-r1", "r1", "reasoning", "qwq", "llama-think"],
        "description": "Deep reasoning, analysis, math, planning, complex thinking",
        "switch_message": "[THINK] Switching to deep reasoning model..."
    }
}


# ── Estado del modelo actual (singleton) ──────────────────────────────────────
_current_active_model = None   # Nombre del modelo cargado actualmente
_available_models_cache = {}   # {engine_name: [model_names]} — actualizado por watchdog
_last_scan_time = 0


def update_available_models(engine_name: str, model_names: list):
    """Called by provider_scanner/watchdog to inform us of available models."""
    global _available_models_cache
    _available_models_cache[engine_name] = model_names


def set_active_model(model_name: str):
    """Called after a successful model switch to track current state."""
    global _current_active_model
    _current_active_model = model_name


def get_active_model() -> str:
    """Returns the currently loaded model name."""
    return _current_active_model


# ── Task Classifier ───────────────────────────────────────────────────────────

def classify_task(text: str, history: list = None) -> str:
    """
    Classifies the task type based on the input text and recent conversation.

    Returns:
        "code"   → Code-specialized model preferred
        "reason" → Reasoning-specialized model preferred
        "any"    → No strong preference, use fastest available
    """
    text_lower = text.lower()
    scores = {"code": 0, "reason": 0}

    # Score against each profile
    for task, profile in TASK_PROFILES.items():
        for keyword, weight in profile["keywords"].items():
            if keyword in text_lower:
                scores[task] += weight

    # Slight context from last conversation turn (lower weight)
    if history and len(history) >= 2:
        last_user = next(
            (m["content"].lower() for m in reversed(history) if m["role"] == "user"),
            ""
        )
        for task, profile in TASK_PROFILES.items():
            for keyword, weight in profile["keywords"].items():
                if keyword in last_user:
                    scores[task] += weight * 0.3  # 30% weight for context

    # Decision threshold: must have a clear winner (≥3 pts difference)
    code_score = scores["code"]
    reason_score = scores["reason"]

    if code_score == 0 and reason_score == 0:
        return "any"
    if code_score >= reason_score + 3:
        return "code"
    if reason_score >= code_score + 3:
        return "reason"
    if code_score > reason_score:
        return "code"   # Code model is faster as default tiebreaker
    if reason_score > code_score:
        return "reason"
    return "any"


# ── Model Ranker ──────────────────────────────────────────────────────────────

def _rank_model(model_name: str, task: str) -> int:
    """Returns a score indicating how suitable a model name is for a given task."""
    name_lower = model_name.lower()
    score = 0

    if task == "code":
        preferred = TASK_PROFILES["code"]["preferred_model_keywords"]
        avoid = TASK_PROFILES["reason"]["preferred_model_keywords"]
    elif task == "reason":
        preferred = TASK_PROFILES["reason"]["preferred_model_keywords"]
        avoid = TASK_PROFILES["code"]["preferred_model_keywords"]
    else:
        return 1  # Any model is fine for generic tasks

    for kw in preferred:
        if kw in name_lower:
            score += 3
    for kw in avoid:
        if kw in name_lower:
            score -= 1  # Soft penalty (not a blocker)

    return score


def find_best_model(task: str, available_models: list) -> str | None:
    """
    From a list of available model names, returns the best one for the given task.
    Falls back to any available model if no specialized one is found.
    """
    if not available_models:
        return None

    # Score all candidates
    ranked = sorted(available_models, key=lambda m: _rank_model(m, task), reverse=True)

    # Use best match if it has a positive score
    best = ranked[0]
    if _rank_model(best, task) > 0:
        return best

    # Fallback: any available model (not currently active, prefer different one if possible)
    alternatives = [m for m in ranked if m != _current_active_model]
    return alternatives[0] if alternatives else ranked[0]


# ── Engine-Specific Model Switchers ──────────────────────────────────────────

def _switch_ollama_model(model_name: str) -> bool:
    """
    For Ollama, switching is implicit: just use the model name in the next request.
    With OLLAMA_MAX_LOADED_MODELS=1, Ollama unloads the old model automatically.
    Returns True always (switching happens at request time).
    """
    global _current_active_model
    _current_active_model = model_name
    return True


def _switch_lemonade_model(model_name: str, ports: list = None) -> bool:
    """
    Switches the active model in Lemonade via /api/v1/load.
    Lemonade unloads the current model before loading the new one (single-model design).
    """
    global _current_active_model
    if ports is None:
        ports = [8000, 8080, 13305]

    for port in ports:
        try:
            payload = json.dumps({"model": model_name}).encode("utf-8")
            req = urllib.request.Request(
                f"http://localhost:{port}/api/v1/load",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=120) as r:  # Loading can take up to 2min
                if r.status in [200, 201, 202]:
                    _current_active_model = model_name
                    return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Try OpenAI-compatible: just change the model in the next request
                _current_active_model = model_name
                return True
        except Exception:
            continue
    return False


def _switch_openai_compatible_model(model_name: str) -> bool:
    """
    For LM Studio / Jan AI / KoboldCPP: model switching requires the user
    to load it in the GUI. We update our tracking and send the model name
    in the next request (the engine may ignore it or use it).
    """
    global _current_active_model
    _current_active_model = model_name
    return True


# ── Main Public API ───────────────────────────────────────────────────────────

def get_optimal_model(
    text: str,
    protocol: str,
    provider_name: str,
    available_models: list,
    history: list = None,
    verbose: bool = True
) -> tuple[str | None, bool]:
    """
    Main entry point. Determines the best model for the given task and
    switches to it if needed.

    Args:
        text:             User's input text
        protocol:         "ollama", "openai", "lemonade", etc.
        provider_name:    Human-readable provider name
        available_models: List of model names available in the engine
        history:          Conversation history for context
        verbose:          Print status messages to console

    Returns:
        (model_name, did_switch)
        - model_name:  The model to use (may be same as current)
        - did_switch:  True if a model switch was performed
    """
    global _current_active_model

    if not available_models:
        return _current_active_model, False

    task = classify_task(text, history)
    best_model = find_best_model(task, available_models)

    if not best_model:
        return _current_active_model, False

    # No switch needed if already using the best model
    if best_model == _current_active_model:
        return best_model, False

    # ── Perform the switch ────────────────────────────────────────────────
    profile = TASK_PROFILES.get(task)
    if verbose and profile and _current_active_model:
        print(f"\n{profile['switch_message']}")
        print(f"  {_current_active_model} → {best_model}")

    lemonade_names = {"lemonade"}
    ollama_names = {"ollama"}

    name_lower = provider_name.lower()
    if any(k in name_lower for k in lemonade_names) or protocol == "lemonade":
        success = _switch_lemonade_model(best_model)
    elif any(k in name_lower for k in ollama_names) or protocol == "ollama":
        success = _switch_ollama_model(best_model)
    else:
        success = _switch_openai_compatible_model(best_model)

    if success:
        return best_model, True
    else:
        # Switch failed; stick with current
        return _current_active_model, False


def describe_selection(text: str, available_models: list) -> str:
    """Returns a human-readable explanation of why a model was selected."""
    task = classify_task(text)
    best = find_best_model(task, available_models)
    task_label = {
        "code": "tarea de código",
        "reason": "razonamiento profundo",
        "any": "consulta general"
    }.get(task, task)
    return f"Tarea: {task_label} → Modelo: {best or 'ninguno disponible'}"


if __name__ == "__main__":
    # Test the classifier with sample inputs
    tests = [
        ("Audita este script de Python para bugs de seguridad", ["qwen2.5-coder-14b", "deepseek-r1-distill-qwen-14b"]),
        ("Por qué los modelos MoE son más eficientes? Explica la arquitectura", ["qwen2.5-coder-14b", "deepseek-r1-distill-qwen-14b"]),
        ("Hola, ¿cómo estás?", ["qwen2.5-coder-14b", "deepseek-r1-distill-qwen-14b"]),
        ("/leer main.rs", ["qwen2.5-coder-14b", "deepseek-r1-distill-qwen-14b"]),
        ("Compara Redis vs PostgreSQL y dame una recomendación", ["qwen2.5-coder-14b", "deepseek-r1-distill-qwen-14b"]),
    ]

    print("\n=== SMART MODEL SELECTOR — Test ===\n")
    for text, models in tests:
        task = classify_task(text)
        best = find_best_model(task, models)
        print(f"  Input : {text[:60]}...")
        print(f"  Task  : {task:<10} → Model: {best}")
        print()
