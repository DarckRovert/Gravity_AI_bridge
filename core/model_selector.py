"""
╔══════════════════════════════════════════════════════════╗
║     GRAVITY AI SMART MODEL SELECTOR V6.0                 ║
║     Selección Inteligente de Modelo por Tarea            ║
╚══════════════════════════════════════════════════════════╝

Decisión automática del modelo óptimo según tipo de tarea.
NUNCA usa dos modelos simultáneamente.

Lógica de selección:
  🔵 Código / Auditoría / Bug   → Qwen2.5-Coder (especialista en código)
  🟠 Razonamiento / Análisis    → DeepSeek-R1   (piensa antes de responder)
  ⚪ General / Conversación     → Modelo activo actual (SIN SWITCH — BUG-07 fix)

V6.0 fixes:
  BUG-07: Tarea 'any' ya no fuerza switch a modelo diferente.
  FEAT-05: Umbral mínimo de score para que un switch ocurra.
  Added: security/crypto audit keywords in 'code' profile.
"""

import json
import os
import urllib.request
import urllib.error
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Task Profiles ─────────────────────────────────────────────────────────────
TASK_PROFILES = {
    "code": {
        "weight": 0,
        "keywords": {
            "/leer": 5, "/leer-carpeta": 5, "/leer-git": 4,
            "código": 3, "code": 3, "bug": 4, "error": 2,
            "función": 3, "function": 3, "clase": 3, "class": 3,
            "script": 3, "refactor": 4, "optimiza": 3, "optimize": 3,
            "audita": 4, "audit": 4, "implementa": 3, "implement": 3,
            "python": 3, "rust": 3, "javascript": 3, "typescript": 3,
            "golang": 3, "java": 3, "c++": 3, "kotlin": 3, "lua": 3,
            ".py": 4, ".rs": 4, ".js": 3, ".ts": 3, ".go": 3,
            "def ": 3, "return ": 2, "import ": 2, "class ": 3,
            "async": 2, "await": 2, "const ": 2, "let ": 2, "var ": 2,
            "test": 2, "unittest": 3, "pytest": 3, "debug": 3,
            "api": 2, "endpoint": 2, "request": 2, "response": 2,
            "sql": 3, "query": 2, "database": 2, "schema": 2,
            "```": 3,
            # Security/crypto audit keywords (FEAT-05 expansion)
            "seguridad": 3, "security": 3, "vulnerabilidad": 4, "vulnerability": 4,
            "criptografía": 4, "cryptography": 4, "cifrado": 3, "encrypt": 3,
            "race condition": 5, "deadlock": 5, "memory leak": 5,
            "unsafe": 4, "zero-trust": 4, "inyección": 4, "injection": 4,
            "exploit": 4, "overflow": 4, "parche": 3, "patch": 3,
        },
        "preferred_model_keywords": ["coder", "code", "starcoder", "codellama", "deepseek-coder"],
        "description": "Code generation, audit, debugging, security, refactoring",
        "switch_message": "[CODE] Switching to code specialist model...",
        "min_score_to_switch": 4,  # FEAT-05: minimum score threshold
    },
    "reason": {
        "weight": 0,
        "keywords": {
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
        "switch_message": "[THINK] Switching to deep reasoning model...",
        "min_score_to_switch": 4,  # FEAT-05: minimum score threshold
    },
}

# ── Module State (singleton) ──────────────────────────────────────────────────
_current_active_model   = None   # Currently loaded model name
_available_models_cache = {}     # {engine_name: [model_names]} — updated by watchdog
_last_scan_time         = 0


def update_available_models(engine_name: str, model_names: list):
    """Called by watchdog to inform us of available models. Deduplicates."""
    global _available_models_cache
    existing = _available_models_cache.get(engine_name, [])
    combined = list(dict.fromkeys(existing + model_names))  # order-preserving dedup
    _available_models_cache[engine_name] = combined


def set_active_model(model_name: str):
    global _current_active_model
    _current_active_model = model_name


def get_active_model():
    return _current_active_model


# ── Task Classifier ───────────────────────────────────────────────────────────

def classify_task(text: str, history: list = None) -> str:
    """
    Classifies the task type from input text + recent conversation context.

    Returns:
        "code"   → code-specialist model preferred
        "reason" → reasoning-specialist model preferred
        "any"    → no strong preference (BUG-07: will NOT trigger a switch)
    """
    text_lower = text.lower()
    scores = {"code": 0, "reason": 0}

    for task, profile in TASK_PROFILES.items():
        for keyword, weight in profile["keywords"].items():
            if keyword in text_lower:
                scores[task] += weight

    # Context bonus from last user turn (30% weight)
    if history and len(history) >= 2:
        last_user = next(
            (m["content"].lower() for m in reversed(history) if m["role"] == "user"),
            ""
        )
        for task, profile in TASK_PROFILES.items():
            for keyword, weight in profile["keywords"].items():
                if keyword in last_user:
                    scores[task] += weight * 0.3

    code_score   = scores["code"]
    reason_score = scores["reason"]

    if code_score == 0 and reason_score == 0:
        return "any"
    if code_score >= reason_score + 3:
        return "code"
    if reason_score >= code_score + 3:
        return "reason"
    if code_score > reason_score:
        return "code"
    if reason_score > code_score:
        return "reason"
    return "any"


# ── Model Ranker ──────────────────────────────────────────────────────────────

def _rank_model(model_name: str, task: str) -> int:
    """Scores how suitable a model name is for a given task type."""
    name_lower = model_name.lower()
    score = 0

    if task == "code":
        preferred = TASK_PROFILES["code"]["preferred_model_keywords"]
        avoid     = TASK_PROFILES["reason"]["preferred_model_keywords"]
    elif task == "reason":
        preferred = TASK_PROFILES["reason"]["preferred_model_keywords"]
        avoid     = TASK_PROFILES["code"]["preferred_model_keywords"]
    else:
        return 1  # Any model is fine

    for kw in preferred:
        if kw in name_lower:
            score += 3
    for kw in avoid:
        if kw in name_lower:
            score -= 1  # Soft penalty

    return score


def find_best_model(task: str, available_models: list):
    """
    Returns the best model name for the given task from available_models.
    Falls back to any available model if no specialized one is found.
    """
    if not available_models:
        return None

    ranked = sorted(available_models, key=lambda m: _rank_model(m, task), reverse=True)
    best   = ranked[0]

    if _rank_model(best, task) > 0:
        return best

    # Fallback: prefer a different model than current (give variety)
    alternatives = [m for m in ranked if m != _current_active_model]
    return alternatives[0] if alternatives else ranked[0]


# ── Engine-Specific Switchers ─────────────────────────────────────────────────

def _switch_ollama_model(model_name: str) -> bool:
    global _current_active_model
    _current_active_model = model_name
    return True


def _switch_lemonade_model(model_name: str, ports: list = None) -> bool:
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
            with urllib.request.urlopen(req, timeout=120) as r:
                if r.status in [200, 201, 202]:
                    _current_active_model = model_name
                    return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                _current_active_model = model_name
                return True
        except Exception:
            continue
    return False


def _switch_openai_compatible_model(model_name: str) -> bool:
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
    verbose: bool = True,
) -> tuple:
    """
    Determines the best model for the task and switches to it if needed.

    Returns:
        (model_name, did_switch)
    """
    global _current_active_model

    if not available_models:
        return _current_active_model, False

    task = classify_task(text, history)

    # BUG-07 / FEAT-05 FIX: 'any' task → NEVER switch, keeps current model stable
    if task == "any":
        return _current_active_model, False

    best_model = find_best_model(task, available_models)

    if not best_model:
        return _current_active_model, False

    # No switch if already on the best model
    if best_model == _current_active_model:
        return best_model, False

    # FEAT-05: Only switch if the best candidate has a meaningful score advantage
    profile   = TASK_PROFILES.get(task, {})
    min_score = profile.get("min_score_to_switch", 3)
    if _rank_model(best_model, task) < min_score:
        return _current_active_model, False

    # Perform the switch
    if verbose and _current_active_model:
        msg = profile.get("switch_message", "[SWITCH]")
        print(f"\n{msg}")
        print(f"  {_current_active_model} → {best_model}")

    lemonade_keys = {"lemonade"}
    ollama_keys   = {"ollama"}

    name_lower = provider_name.lower()
    if any(k in name_lower for k in lemonade_keys) or protocol == "lemonade":
        success = _switch_lemonade_model(best_model)
    elif any(k in name_lower for k in ollama_keys) or protocol == "ollama":
        success = _switch_ollama_model(best_model)
    else:
        success = _switch_openai_compatible_model(best_model)

    return (best_model, True) if success else (_current_active_model, False)


def describe_selection(text: str, available_models: list) -> str:
    task  = classify_task(text)
    best  = find_best_model(task, available_models)
    label = {
        "code":   "tarea de código",
        "reason": "razonamiento profundo",
        "any":    "consulta general (sin switch)",
    }.get(task, task)
    return f"Tarea: {label} → Modelo: {best or 'ninguno disponible'}"


if __name__ == "__main__":
    tests = [
        ("Audita este script de Python para bugs de seguridad",
         ["qwen2.5-coder-14b", "deepseek-r1-distill-qwen-14b"]),
        ("Por qué los modelos MoE son más eficientes?",
         ["qwen2.5-coder-14b", "deepseek-r1-distill-qwen-14b"]),
        ("Hola, ¿cómo estás?",
         ["qwen2.5-coder-14b", "deepseek-r1-distill-qwen-14b"]),
        ("/leer main.rs",
         ["qwen2.5-coder-14b", "deepseek-r1-distill-qwen-14b"]),
        ("Compara Redis vs PostgreSQL",
         ["qwen2.5-coder-14b", "deepseek-r1-distill-qwen-14b"]),
    ]

    print("\n=== SMART MODEL SELECTOR V6.0 — Test ===\n")
    for text, models in tests:
        set_active_model("qwen2.5-coder-14b")
        task  = classify_task(text)
        best  = find_best_model(task, models)
        print(f"  Input : {text[:60]}")
        print(f"  Task  : {task:<10} → Model: {best}")
        print()
