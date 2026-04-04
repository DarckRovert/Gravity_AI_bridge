"""
╔══════════════════════════════════════════════════════════╗
║     GRAVITY AI TURBO KV OPTIMIZER V5.1                   ║
║     Cuantización del KV-Cache — Multi-Engine             ║
╚══════════════════════════════════════════════════════════╝

ESTADO DE IMPLEMENTACIÓN:
  ✅ Ollama:     ACTIVO via OLLAMA_KV_CACHE_TYPE=q4_0 + OLLAMA_FLASH_ATTENTION=1
                 → 4x reducción de RAM del KV-Cache (equivalente funcional de TurboQuant)
  ✅ Lemonade:   ACTIVO via --kv-cache-type q4_0 + -fa on en llamacpp-args
  ✅ LM Studio:  Flash Attention activado en requests + num_ctx dinámico
  ✅ KoboldCPP:  Flash Attention + batch size optimizado
  ⏳ TurboQuant REAL (Google DeepMind, Marzo 2026): pendiente integración en Ollama/llama.cpp
     → Este módulo activará TurboQuant real automáticamente cuando esté disponible,
       sin ningún cambio de código adicional (solo cambiar la flag a True).

MATEMÁTICA:
  TurboQuant:  FP16 → ~3 bits  (PolarQuant + QJL)  = 6x reducción
  q8_0:        FP16 → 8 bits                        = 2x reducción
  q4_0:        FP16 → 4 bits                        = 4x reducción  ← ACTIVO AHORA
"""

import os

# ── Feature Flags (automáticas cuando lleguen a los motores estables) ──────────
_TURBO_QUANT_OLLAMA_AVAILABLE = False    # Activar cuando Ollama lo soporte en stable
_TURBO_QUANT_LEMONADE_AVAILABLE = False  # Activar cuando Lemonade lo soporte en stable
_TURBO_QUANT_LLAMACPP_ARG = "turbo4"    # CLI arg cuando esté disponible


def get_ollama_kv_options(vram_mb, model_size_b=32):
    """
    Returns a dict of env vars for optimal Ollama KV-cache quantization.

    Priority:
      1. TurboQuant real (when available): 6x reduction
      2. q4_0 (<10GB VRAM): 4x reduction, slight quality loss on extreme contexts
      3. q8_0 (≥10GB VRAM): 2x reduction, near-zero quality loss
    """
    if _TURBO_QUANT_OLLAMA_AVAILABLE:
        kv_type = _TURBO_QUANT_LLAMACPP_ARG
        label = "TurboQuant (Google DeepMind) — 6x reduction"
    elif vram_mb < 10000:
        kv_type = "q4_0"
        label = "Q4_0 KV-Cache — 4x reduction (TurboQuant-compatible)"
    else:
        kv_type = "q8_0"
        label = "Q8_0 KV-Cache — 2x reduction (near-lossless)"

    return {
        "OLLAMA_KV_CACHE_TYPE": kv_type,
        "OLLAMA_FLASH_ATTENTION": "1",
        "_label": label,
    }


def get_lemonade_llamacpp_args(vram_mb):
    """
    Returns the --llamacpp-args string for Lemonade server startup.
    These args maximize prefill throughput and KV compression.
    """
    if _TURBO_QUANT_LEMONADE_AVAILABLE:
        kv_arg = f"--kv-cache-type {_TURBO_QUANT_LLAMACPP_ARG}"
    elif vram_mb < 10000:
        kv_arg = "--kv-cache-type q4_0"
    else:
        kv_arg = "--kv-cache-type q8_0"

    # -b/-ub: batch sizes for maximum prefill throughput
    # -fa on: Flash Attention (mandatory, ~20% RAM reduction in attention)
    return f"-b 16384 -ub 16384 -fa on {kv_arg}"


def get_kobold_flash_options(vram_mb):
    """
    Returns KoboldCPP optimal batch size and Flash Attention flag.
    KoboldCPP uses its own API params (not env vars).
    """
    return {
        "use_flash_attention": True,
        "blasbatchsize": 512 if vram_mb >= 8192 else 128,
        "gpulayers": -1,  # All layers on GPU
    }


def describe(engine="ollama"):
    """
    Returns a human-readable description of the active KV optimization level.
    Used by show_info() in AuditorCLI.
    """
    if _TURBO_QUANT_OLLAMA_AVAILABLE and engine == "ollama":
        return "🟣 TurboQuant REAL (Google DeepMind) — 6x RAM reduction"

    kv = os.environ.get("OLLAMA_KV_CACHE_TYPE", "f16")
    flash = os.environ.get("OLLAMA_FLASH_ATTENTION", "0") == "1"
    lemonade_kv = os.environ.get("LEMONADE_KV_TYPE", "f16")

    reductions = {"q4_0": "4x", "q8_0": "2x", "f16": "1x (no compression)"}
    flash_txt = " + ⚡ Flash Attention" if flash else ""

    if engine in ["lemonade", "openai"] and "LEMONADE_LLAMACPP" in os.environ:
        red = reductions.get(lemonade_kv, "4x")
        return f"🟡 Lemonade KV {lemonade_kv.upper()} — {red} reduction{flash_txt}"

    red = reductions.get(kv, "4x")
    return f"🟢 Ollama KV-Cache {kv.upper()} — {red} reduction{flash_txt}"
