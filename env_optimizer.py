"""
╔══════════════════════════════════════════════════════════╗
║     GRAVITY AI ENVIROMENT OPTIMIZER V7.0                 ║
║     Optimización Automática para TODOS los Motores       ║
╚══════════════════════════════════════════════════════════╝

Motores soportados:
  🧠 Ollama      → Variables de entorno del Sistema Operativo
  🍋 Lemonade    → Env vars + pre-warm via /api/v1/load
  🎬 LM Studio   → Parámetros de API (no admite env vars externas)
  ⚖️  KoboldCPP  → Parámetros de API (configura por flags CLI)
  🌙 Jan AI      → Parámetros de API (ngl, ctx_len)

Uso:
  python env_optimizer.py            → Solo inyecta en sesión actual
  python env_optimizer.py --persist  → Persiste en Windows Registry (setx)
"""

import os
import sys
import json
import subprocess
import urllib.request
import urllib.error
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _safe_get(url, timeout=2):
    """HTTP GET que nunca lanza excepciones."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", errors="ignore"))
    except Exception:
        return None


def _safe_post(url, payload, timeout=5):
    """HTTP POST que nunca lanza excepciones."""
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except Exception:
        return None


def _set_env(key, value, persist=False):
    """
    Sets a process-level env var ONLY if the user hasn't already set it.
    This respects manual user configurations (like the ones in the screenshot).
    If persist=True, writes to Windows user environment via setx.
    """
    if key not in os.environ:
        os.environ[key] = str(value)
        if persist and sys.platform == "win32":
            try:
                subprocess.run(
                    f'setx {key} "{value}"',
                    shell=True, capture_output=True, timeout=5
                )
            except Exception:
                pass
        return True  # It was newly set
    return False  # Already set by user, respected


def _load_hardware():
    """Loads the hardware profile, falling back to safe defaults."""
    try:
        from hardware_profiler import get_full_profile
        return get_full_profile()
    except Exception:
        return {
            "vendor": "unknown", "vram_mb": 8192, "is_igpu": False,
            "gpu_type": "cpu", "gfx_version": None, "optimal_ctx": 32768,
            "kv_quant": "q4_0", "is_amd": False, "is_nvidia": False,
            "total_ram_mb": 32768, "model_size_b": 32, "gpu_name": "Unknown",
        }


# ─── Per-Engine Optimizers ───────────────────────────────────────────────────

def apply_ollama(profile, persist=False):
    """Injects optimal Ollama env vars. Does NOT overwrite user-set variables."""
    from turbo_kv import get_ollama_kv_options

    kv_opts = get_ollama_kv_options(profile["vram_mb"], profile["model_size_b"])

    _set_env("OLLAMA_FLASH_ATTENTION", kv_opts["OLLAMA_FLASH_ATTENTION"], persist)
    _set_env("OLLAMA_KV_CACHE_TYPE", kv_opts["OLLAMA_KV_CACHE_TYPE"], persist)
    _set_env("OLLAMA_NUM_PARALLEL", "1", persist)
    _set_env("OLLAMA_SCHED_SPREAD", "1", persist)
    _set_env("OLLAMA_MAX_LOADED_MODELS", "1", persist)
    _set_env("OLLAMA_ORIGINS", "*", persist)

    if profile["is_amd"]:
        _set_env("OLLAMA_VULKAN", "1", persist)
        _set_env("OLLAMA_LLM_LIBRARY", "rocm", persist)
        if profile.get("gfx_version"):
            _set_env("HSA_OVERRIDE_GFX_VERSION", profile["gfx_version"], persist)
    elif profile["is_nvidia"]:
        _set_env("OLLAMA_LLM_LIBRARY", "cuda", persist)
    # CPU fallback: no specific library needed


def apply_lemonade(profile, persist=False):
    """Injects Lemonade-specific env vars."""
    if profile["is_amd"]:
        _set_env("LEMONADE_LLAMACPP", "rocm", persist)
        if not profile["is_igpu"]:
            _set_env("LEMONADE_ENABLE_DGPU_GTT", "1", persist)
        # Pass the ROCm GFX version for Lemonade's llama.cpp backend too
        if profile.get("gfx_version"):
            _set_env("HSA_OVERRIDE_GFX_VERSION", profile["gfx_version"], persist)
    elif profile["is_nvidia"]:
        _set_env("LEMONADE_LLAMACPP", "cuda", persist)
    else:
        _set_env("LEMONADE_LLAMACPP", "cpu", persist)

    # Tell ROCm to use Vulkan as fallback for iGPU if dGPU isn't found
    if profile["is_igpu"] and profile["is_amd"]:
        _set_env("LEMONADE_LLAMACPP", "vulkan", persist)  # More stable for iGPU


def prewarm_lemonade(model_name=None):
    """
    Pre-loads the target model in Lemonade to eliminate the TTFT cold-start spike.
    Lemonade's /api/v1/load is the official endpoint for pre-loading.
    """
    if not model_name:
        try:
            with open(os.path.join(BASE_DIR, "_settings.json"), "r", encoding="utf-8") as f:
                model_name = json.load(f).get("last_model", "")
        except Exception:
            return False

    if not model_name:
        return False

    for port in [8000, 8080, 13305]:
        # Health check first
        health = _safe_get(f"http://localhost:{port}/health", timeout=1)
        if health is None:
            health = _safe_get(f"http://localhost:{port}/v1/models", timeout=1)
        if health is None:
            continue

        # Pre-load model
        status = _safe_post(
            f"http://localhost:{port}/api/v1/load",
            {"model": model_name},
            timeout=10
        )
        if status in [200, 201, 202]:
            return True
        # Also try OpenAI-compatible endpoint
        _safe_post(
            f"http://localhost:{port}/v1/chat/completions",
            {"model": model_name, "messages": [], "max_tokens": 1},
            timeout=5
        )
        return True  # Lemonade is listening; prewarm attempted

    return False


def get_lm_studio_model_ctx(port=1234):
    """
    Queries LM Studio's /v1/models to get the max context of the loaded model.
    LM Studio returns context_length in the model object metadata.
    Returns None if LM Studio is not running or the field is absent.
    """
    data = _safe_get(f"http://localhost:{port}/v1/models", timeout=2)
    if not data:
        return None
    models = data.get("data", [])
    if not models:
        return None
    m = models[0]
    # Different LMS versions use different field names
    for field in ["max_context_length", "context_length", "n_ctx", "max_tokens"]:
        if m.get(field):
            return int(m[field])
    return None


def get_kobold_active_params(port=5001):
    """
    Reads KoboldCPP's active configuration via its /api/extra/version endpoint.
    Returns dict with detected params (gpulayers, contextsize, etc.)
    """
    data = _safe_get(f"http://localhost:{port}/api/extra/version", timeout=2)
    if not data:
        return {}
    # KoboldCPP exposes its config via /api/v1/config (if available)
    config = _safe_get(f"http://localhost:{port}/api/v1/config", timeout=2)
    return config or {}


# ─── Unified API Options Builder ─────────────────────────────────────────────

def build_api_options(engine_name, profile, user_opts=None):
    """
    Builds the optimal API options dict for a given engine.
    This dict goes into every AI request made by AuditorCLI.

    Each engine supports different API params; this function normalizes them.
    """
    opts = user_opts.copy() if user_opts else {}
    ctx = profile["optimal_ctx"]

    if engine_name == "ollama":
        # Ollama accepts these in the 'options' sub-dict
        opts.setdefault("num_ctx", ctx)
        opts.setdefault("temperature", 0.6)
        opts.setdefault("streaming", True)

    elif engine_name in ["openai", "lm_studio", "lemonade"]:
        # OpenAI-compatible engines
        opts.setdefault("num_ctx", ctx)
        opts.setdefault("temperature", 0.6)
        opts.setdefault("streaming", True)
        # LM Studio supports prompt caching (re-uses KV-cache for repeated system prompts)
        opts.setdefault("cache_prompt", True)

    elif engine_name == "kobold":
        # KoboldCPP uses different param names
        opts.setdefault("max_length", min(ctx, 4096))
        opts.setdefault("temperature", 0.6)

    elif engine_name == "jan":
        # Jan AI OpenAI-compatible
        opts.setdefault("num_ctx", ctx)
        opts.setdefault("ngl", -1)  # All GPU layers
        opts.setdefault("n_batch", 512)
        opts.setdefault("temperature", 0.6)

    return opts


# ─── Main Entry Point ─────────────────────────────────────────────────────────

def apply_all(persist=False, verbose=False):
    """
    Master function. Detects hardware, applies env vars for ALL engines,
    optionally pre-warms Lemonade, and returns the hardware profile +
    the optimized API options for the currently active engine.

    Called by:
      - engine_watchdog.py at startup and on every scan cycle
      - INSTALAR.bat with --persist for permanent configuration
    """
    profile = _load_hardware()

    if verbose:
        print(f"\n[⚡ EnvOptimizer V7.0]")
        print(f"  GPU    : {profile.get('gpu_name', 'Unknown')}")
        print(f"  VRAM   : {profile['vram_mb']:,} MB")
        print(f"  Ctx    : {profile['optimal_ctx']:,} tokens (KV: {profile['kv_quant']})")

    # Apply env vars for each engine
    apply_ollama(profile, persist=persist)
    apply_lemonade(profile, persist=persist)
    # LM Studio uses no env vars; we handle it via API params in build_api_options

    # Check if LM Studio is running and constrain ctx to its actual model limit
    lms_ctx = get_lm_studio_model_ctx()
    if lms_ctx and lms_ctx < profile["optimal_ctx"]:
        if verbose:
            print(f"  LM Studio model max ctx detected: {lms_ctx:,} tokens → using that limit")
        profile["optimal_ctx"] = lms_ctx

    # Try to pre-warm Lemonade (non-blocking, fails silently)
    prewarm_lemonade()

    # Build default API options (for Ollama; watchdog will override per engine)
    api_opts = build_api_options("ollama", profile)

    if verbose:
        applied_vars = {
            k: os.environ.get(k, "(not set)")
            for k in ["OLLAMA_FLASH_ATTENTION", "OLLAMA_KV_CACHE_TYPE", "OLLAMA_VULKAN",
                       "OLLAMA_LLM_LIBRARY", "HSA_OVERRIDE_GFX_VERSION", "LEMONADE_LLAMACPP",
                       "LEMONADE_ENABLE_DGPU_GTT"]
            if os.environ.get(k)
        }
        if applied_vars:
            print("\n  Env vars activas:")
            for k, v in applied_vars.items():
                print(f"    {k} = {v}")

    return profile, api_opts


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    persist = "--persist" in sys.argv
    profile, api_opts = apply_all(persist=persist, verbose=True)

    print("\n  Parámetros API óptimos (Ollama):")
    for k, v in api_opts.items():
        print(f"    {k}: {v}")

    if persist:
        print("\n  [✅] Variables persistidas permanentemente via setx (reinicia Ollama para que tome efecto).")
    else:
        print("\n  Tip: Usa 'python env_optimizer.py --persist' para guardar permanentemente.")
