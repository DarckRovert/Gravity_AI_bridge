"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         GRAVITY AI — ENV OPTIMIZER V1.0                                      ║
║         Optimización de parámetros de API basada en hardware real            ║
╚══════════════════════════════════════════════════════════════════════════════╝

Exporta:
  apply_all(persist, verbose) -> (profile_dict, api_opts_dict)
  build_api_options(engine_key, profile, user_opts) -> dict

Usado por engine_watchdog.py para calcular num_ctx, threads y GPU layers
óptimos en función del hardware detectado por hardware_profiler.
"""

import os
import logging
import threading
from typing import Dict, Tuple

log = logging.getLogger("gravity.env_optimizer")
_settings_lock = threading.RLock()

# ── Parámetros por motor ───────────────────────────────────────────────────────

# Cada engine_key tiene su propio nombre de parámetro para contexto y threads.
_ENGINE_CTX_KEY: Dict[str, str] = {
    "ollama":        "num_ctx",
    "lm_studio":     "n_ctx",
    "kobold":        "max_context_length",
    "jan":           "n_ctx",
    "lemonade":      "max_new_tokens",
    "openai_compat": "max_tokens",
}

_ENGINE_THREAD_KEY: Dict[str, str] = {
    "ollama":    "num_thread",
    "lm_studio": "threads",
    "kobold":    "usemlock",   # kobold no tiene threads API — se omite
    "jan":       "threads",
    "lemonade":  "num_threads",
}

_ENGINE_GPU_KEY: Dict[str, str] = {
    "ollama":    "num_gpu",
    "lm_studio": "n_gpu_layers",
    "kobold":    "gpulayers",
    "jan":       "n_gpu_layers",
    "lemonade":  "gpu_layers",
}


# ── Lógica de cálculo ─────────────────────────────────────────────────────────

def _compute_optimal_params(profile: dict) -> dict:
    """
    Calcula num_ctx, threads y gpu_layers óptimos dado un perfil de hardware.
    """
    total_ram_mb: int = profile.get("total_ram_mb", 16384)
    vram_mb: int      = profile.get("vram_mb", 8192)
    optimal_ctx: int  = profile.get("optimal_ctx", 0)

    # ── num_ctx por RAM del sistema ────────────────────────────────────────────
    if optimal_ctx > 0:
        num_ctx = optimal_ctx
    elif total_ram_mb >= 32768:   # >= 32 GB
        num_ctx = 16384
    elif total_ram_mb >= 16384:   # >= 16 GB
        num_ctx = 8192
    else:
        num_ctx = 4096

    # ── CPU threads: núcleos físicos - 2, mínimo 2 ────────────────────────────
    import os as _os
    total_cores = _os.cpu_count() or 4
    # os.cpu_count() da hilos lógicos en Windows; dividir por 2 para físicos
    physical_cores = max(total_cores // 2, 2)
    num_thread = max(physical_cores - 2, 2)

    # ── GPU layers: calcular cuántas capas caben en VRAM ─────────────────────
    # Heurística conservadora: 1 GB de VRAM ≈ 4 capas para models 7-14B
    if vram_mb >= 8192:
        num_gpu = max(int(vram_mb / 1024) * 4, 16)
    elif vram_mb >= 4096:
        num_gpu = 8
    else:
        num_gpu = 0  # CPU puro

    return {
        "num_ctx":    num_ctx,
        "num_thread": num_thread,
        "num_gpu":    num_gpu,
    }


# ── API Pública ────────────────────────────────────────────────────────────────

def build_api_options(engine_key: str, profile: dict, user_opts: dict) -> dict:
    """
    Construye el dict de opciones de API para el engine dado.
    user_opts siempre tiene prioridad sobre los valores calculados.

    Args:
        engine_key: "ollama" | "lm_studio" | "kobold" | "jan" | "lemonade" | "openai_compat"
        profile: dict de hardware (salida de hardware_profiler.get_full_profile())
        user_opts: dict de overrides del usuario (de _settings.json > advanced_params)

    Returns:
        dict con parámetros listos para usar en la petición de API.
    """
    computed = _compute_optimal_params(profile)
    opts: dict = {}

    ctx_key    = _ENGINE_CTX_KEY.get(engine_key, "num_ctx")
    thread_key = _ENGINE_THREAD_KEY.get(engine_key)
    gpu_key    = _ENGINE_GPU_KEY.get(engine_key)

    opts[ctx_key] = computed["num_ctx"]
    if thread_key and engine_key != "kobold":
        opts[thread_key] = computed["num_thread"]
    if gpu_key:
        opts[gpu_key] = computed["num_gpu"]

    # Ollama-specific extras
    if engine_key == "ollama":
        opts["num_keep"]    = 24
        opts["repeat_last_n"] = 64

    # user_opts sobreescribe todo (el usuario siempre gana)
    for k, v in user_opts.items():
        opts[k] = v

    return opts


def apply_all(persist: bool = True, verbose: bool = False) -> Tuple[dict, dict]:
    """
    Detecta el hardware, calcula los parámetros óptimos y opcionalmente
    persiste num_ctx en _settings.json.

    Returns:
        (profile_dict, api_opts_dict) donde api_opts usa claves de Ollama por defecto.
    """
    profile: dict = {}
    try:
        from core.hardware_profiler import get_full_profile
        profile = get_full_profile()
    except Exception as e:
        log.warning(f"[EnvOptimizer] hardware_profiler no disponible: {e}")
        profile = {
            "total_ram_mb": 16384,
            "vram_mb":      8192,
            "optimal_ctx":  8192,
            "gpu_type":     "cpu",
        }

    user_opts: dict = {}
    settings = {}
    try:
        import json as _json
        _BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        settings_path = os.path.join(_BASE, "_settings.json")
        with _settings_lock:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = _json.load(f)
        user_opts = settings.get("advanced_params", {})
    except Exception:
        pass

    # Detectar engine activo para construir con las keys correctas
    engine_key = "ollama"
    try:
        engine_key = settings.get("provider_protocol", "ollama") or "ollama"
    except Exception:
        pass

    api_opts = build_api_options(engine_key, profile, user_opts)

    if persist:
        try:
            import json as _json
            _BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            settings_path = os.path.join(_BASE, "_settings.json")
            with _settings_lock:
                try:
                    with open(settings_path, "r", encoding="utf-8") as f:
                        data = _json.load(f)
                except Exception:
                    data = {}
                adv = data.get("advanced_params", {})
                # Solo actualiza num_ctx si el nuevo valor es mayor
                new_ctx = api_opts.get("num_ctx", 0)
                if new_ctx > adv.get("num_ctx", 0):
                    adv["num_ctx"] = new_ctx
                    data["advanced_params"] = adv
                    with open(settings_path, "w", encoding="utf-8") as f:
                        _json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            log.debug(f"[EnvOptimizer] No se pudo persistir settings: {e}")

    if verbose:
        log.info(
            f"[EnvOptimizer] RAM={profile.get('total_ram_mb', '?')}MB | "
            f"VRAM={profile.get('vram_mb', '?')}MB | "
            f"num_ctx={api_opts.get('num_ctx', '?')} | "
            f"threads={api_opts.get('num_thread', '?')} | "
            f"gpu={api_opts.get('num_gpu', '?')}"
        )

    return profile, api_opts
