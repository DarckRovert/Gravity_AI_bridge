"""
╔══════════════════════════════════════════════════════╗
║     GRAVITY AI HARDWARE PROFILER V5.1                ║
║     Detección de GPU, VRAM y cálculo de contexto     ║
╚══════════════════════════════════════════════════════╝
Detecta el hardware disponible y calcula el num_ctx máximo
que puede correr sin colapsar la RAM del sistema.
"""

import subprocess
import platform
import os
import json
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Mapa de modelos AMD iGPU conocidos → versión GFX para ROCm
AMD_GFX_MAP = {
    "890m": "12.0.0",   # Strix Halo
    "880m": "11.5.0",   # Hawk Point 2
    "780m": "11.0.0",   # Phoenix (Ryzen 7 8700G)
    "760m": "11.0.0",   # Phoenix
    "740m": "11.0.0",   # Phoenix
    "680m": "10.3.5",   # Van Gogh (Steam Deck)
    "rx 7900": "11.0.0",
    "rx 7800": "11.0.0",
    "rx 7700": "11.0.0",
    "rx 7600": "11.0.3",
    "rx 6900": "10.3.2",
    "rx 6800": "10.3.2",
    "rx 6700": "10.3.2",
    "rx 6600": "10.3.1",
    "rx 6500": "10.3.1",
}


def _run_cmd(cmd, timeout=4):
    """Runs a shell command and returns stdout, suppressing all errors."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, shell=True, encoding="utf-8", errors="ignore"
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _detect_amd_gfx(gpu_name_lower):
    """Returns the ROCm GFX version string for the detected AMD GPU."""
    for model, gfx in AMD_GFX_MAP.items():
        if model in gpu_name_lower:
            return gfx
    return "11.0.0"  # Safe modern AMD default


def _parse_gpu_windows():
    """Parses GPU info on Windows using Get-CimInstance (WMIC deprecated in Win11)."""
    gpus = []
    ps_cmd = (
        "Get-CimInstance -ClassName Win32_VideoController "
        "| Select-Object Name,AdapterRAM "
        "| ConvertTo-Csv -NoTypeInformation"
    )
    out = _run_cmd(f'powershell -NoProfile -Command "{ps_cmd}"', timeout=5)
    for line in out.splitlines():
        line = line.strip().strip('"')
        if not line or line.startswith("Name"):
            continue
        # CSV: "Name","AdapterRAM"
        parts = [p.strip().strip('"') for p in line.split('","')]
        if len(parts) >= 2:
            try:
                name = parts[0]
                vram_bytes = int(parts[1]) if parts[1].isdigit() else 0
                if name:
                    gpus.append({"name": name, "vram_bytes": vram_bytes})
            except Exception:
                continue
    return gpus


def _parse_ram_windows():
    """Returns total system RAM in MB using Get-CimInstance (Windows 11 compatible)."""
    ps_cmd = (
        "(Get-CimInstance -ClassName Win32_ComputerSystem).TotalPhysicalMemory"
    )
    out = _run_cmd(f'powershell -NoProfile -Command "{ps_cmd}"', timeout=5)
    try:
        return int(out.strip()) // (1024 ** 2)
    except Exception:
        return 32768  # fallback 32GB


def _parse_gpu_linux():
    """Parses GPU info on Linux using lspci and rocm-smi/nvidia-smi."""
    gpus = []
    lspci = _run_cmd("lspci 2>/dev/null | grep -iE 'vga|3d|display'")
    if lspci:
        gpus.append({"name": lspci.split(":")[-1].strip(), "vram_bytes": 0})
    return gpus


def _parse_ram_linux():
    """Returns total system RAM in MB on Linux."""
    out = _run_cmd("grep MemTotal /proc/meminfo 2>/dev/null")
    try:
        return int(re.search(r'\d+', out).group()) // 1024
    except Exception:
        return 16384


def detect_gpu():
    """
    Returns a hardware profile dict with all GPU/RAM data needed
    by env_optimizer and turbo_kv to make their decisions.
    """
    profile = {
        "gpu_name": "Unknown",
        "vendor": "unknown",          # amd | nvidia | intel | unknown
        "vram_mb": 8192,              # Fallback: 8GB
        "total_ram_mb": 16384,        # Fallback: 16GB
        "is_igpu": False,
        "gpu_type": "cpu",            # cuda | rocm | vulkan | cpu
        "gfx_version": None,          # AMD GFX version for ROCm
    }

    is_windows = platform.system() == "Windows"
    gpus = _parse_gpu_windows() if is_windows else _parse_gpu_linux()
    profile["total_ram_mb"] = _parse_ram_windows() if is_windows else _parse_ram_linux()

    # Select the primary GPU (prefer dedicated over integrated)
    best_gpu = None
    for g in gpus:
        if best_gpu is None or g["vram_bytes"] > best_gpu["vram_bytes"]:
            best_gpu = g

    if best_gpu:
        profile["gpu_name"] = best_gpu["name"]
        profile["vram_mb"] = best_gpu["vram_bytes"] // (1024 ** 2) if best_gpu["vram_bytes"] > 0 else 0
        name_lower = best_gpu["name"].lower()

        if "amd" in name_lower or "radeon" in name_lower:
            profile["vendor"] = "amd"
            profile["gpu_type"] = "rocm"
            # Detect iGPU keywords
            igpu_keywords = ["780m", "760m", "740m", "890m", "880m", "680m",
                             "integrated", "igpu", "vega", "raphael", "phoenix"]
            profile["is_igpu"] = any(k in name_lower for k in igpu_keywords)
            profile["gfx_version"] = _detect_amd_gfx(name_lower)

        elif any(x in name_lower for x in ["nvidia", "geforce", "rtx", "gtx", "quadro"]):
            profile["vendor"] = "nvidia"
            profile["gpu_type"] = "cuda"

        elif "intel" in name_lower:
            profile["vendor"] = "intel"
            profile["gpu_type"] = "vulkan"
            profile["is_igpu"] = True

    # iGPU with shared memory: use 35% of system RAM as effective VRAM estimate.
    # AMD 780M / Intel Arc iGPU drivers report only 512MB (or similar fictitious value).
    # Real VRAM is whatever the BIOS allocates from system RAM — usually 2-16GB.
    if profile["is_igpu"] and profile["vram_mb"] < 8192:
        profile["vram_mb"] = int(profile["total_ram_mb"] * 0.35)

    return profile


def calculate_optimal_ctx(vram_mb, model_size_b=32, kv_quant="q4_0"):
    """
    Calculates the maximum context window that fits in available VRAM.

    Based on KV-cache memory requirements (per token):
      - FP16 (f16):  ~0.500 MB × model_size_B
      - Q8_0 (q8_0): ~0.250 MB × model_size_B  (2× reduction)
      - Q4_0 (q4_0): ~0.125 MB × model_size_B  (4× reduction, TurboQuant-style)

    We allocate 45% of VRAM to the KV-cache, leaving the rest for model weights and overhead.
    """
    quant_mb_per_token = {"f16": 0.500, "q8_0": 0.250, "q4_0": 0.125}
    kv_mb_per_token = quant_mb_per_token.get(kv_quant, 0.125) * model_size_b
    available_for_kv_mb = vram_mb * 0.45

    if kv_mb_per_token <= 0:
        return 8192

    ctx = int(available_for_kv_mb / kv_mb_per_token)

    # Snap to standard context sizes
    for threshold in [131072, 65536, 32768, 16384, 8192, 4096, 2048]:
        if ctx >= threshold:
            return threshold
    return 2048


def get_full_profile():
    """
    Main function. Returns the complete hardware profile dict,
    including optimal context window for the currently configured model.
    """
    gpu = detect_gpu()

    # Detect current model size from settings
    model_size_b = 32  # Default: 32B
    try:
        settings_file = os.path.join(BASE_DIR, "_settings.json")
        with open(settings_file, "r", encoding="utf-8") as f:
            settings = json.load(f)
        model_name = settings.get("last_model", "").lower()
        for size_str, size_b in [("70b", 70), ("72b", 72), ("32b", 32), ("30b", 30),
                                   ("14b", 14), ("13b", 13), ("8b", 8), ("7b", 7), ("3b", 3), ("1b", 1)]:
            if size_str in model_name:
                model_size_b = size_b
                break
    except Exception:
        pass

    # Choose KV quantization based on VRAM
    kv_quant = "q4_0" if gpu["vram_mb"] < 10000 else "q8_0"
    optimal_ctx = calculate_optimal_ctx(gpu["vram_mb"], model_size_b, kv_quant)

    return {
        **gpu,
        "model_size_b": model_size_b,
        "kv_quant": kv_quant,
        "optimal_ctx": optimal_ctx,
        "is_amd": gpu["vendor"] == "amd",
        "is_nvidia": gpu["vendor"] == "nvidia",
    }


if __name__ == "__main__":
    print("\n╔══════════════════════════════════╗")
    print("║  GRAVITY AI HARDWARE PROFILER    ║")
    print("╚══════════════════════════════════╝\n")

    p = get_full_profile()
    print(f"  GPU           : {p['gpu_name']}")
    print(f"  Vendor        : {p['vendor'].upper()}")
    print(f"  Tipo          : {'iGPU (Integrada)' if p['is_igpu'] else 'dGPU (Dedicada)'}")
    print(f"  VRAM Estimada : {p['vram_mb']:,} MB ({p['vram_mb']//1024:.1f} GB)")
    print(f"  RAM Total     : {p['total_ram_mb']:,} MB ({p['total_ram_mb']//1024:.0f} GB)")
    print(f"  GPU Backend   : {p['gpu_type'].upper()}")
    if p.get("gfx_version"):
        print(f"  GFX Version   : {p['gfx_version']} (ROCm compat)")
    print(f"\n  Modelo ({p['model_size_b']}B)  : {p['kv_quant'].upper()} KV-Cache")
    print(f"  Contexto Óptimo     : {p['optimal_ctx']:,} tokens")
    print()
