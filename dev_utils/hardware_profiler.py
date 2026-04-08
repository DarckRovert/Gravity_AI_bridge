"""
╔══════════════════════════════════════════════════════╗
║     GRAVITY AI — HARDWARE PROFILER V7.1              ║
║     Detección multi-GPU, VRAM y cálculo de contexto  ║
╚══════════════════════════════════════════════════════╝
Detecta TODAS las GPUs disponibles (iGPU + dGPU),
selecciona la GPU primaria (mayor VRAM dGPU dedicada)
y calcula el num_ctx máximo óptimo para el hardware.

V6.0 fixes: csv.reader para GPU names con comas (BUG-11),
            soporte multi-GPU + campo all_gpus (FEAT-14).
"""

import subprocess
import platform
import os
import json
import re
import csv
import io

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Mapa de modelos AMD iGPU conocidos → versión GFX para ROCm
AMD_GFX_MAP = {
    "890m":    "12.0.0",   # Strix Halo
    "880m":    "11.5.0",   # Hawk Point 2
    "780m":    "11.0.0",   # Phoenix (Ryzen 7 8700G)
    "760m":    "11.0.0",   # Phoenix
    "740m":    "11.0.0",   # Phoenix
    "680m":    "10.3.5",   # Van Gogh (Steam Deck)
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
    """
    Parses GPU info on Windows using Get-CimInstance and csv.reader.
    BUG-11 FIX: uses csv.reader instead of manual split to handle
    GPU names containing commas (e.g. 'NVIDIA GeForce RTX 4090, Creator Edition').
    """
    gpus = []
    ps_cmd = (
        "Get-CimInstance -ClassName Win32_VideoController "
        "| Select-Object Name,AdapterRAM "
        "| ConvertTo-Csv -NoTypeInformation"
    )
    out = _run_cmd(f'powershell -NoProfile -Command "{ps_cmd}"', timeout=6)
    if not out:
        return gpus

    reader = csv.reader(io.StringIO(out))
    header_skipped = False
    for row in reader:
        if not header_skipped:
            header_skipped = True
            continue
        if len(row) >= 2:
            try:
                name = row[0].strip().strip('"')
                vram_str = row[1].strip().strip('"')
                vram_bytes = int(vram_str) if vram_str.isdigit() else 0
                if name and name.lower() not in ("name", ""):
                    gpus.append({"name": name, "vram_bytes": vram_bytes})
            except Exception:
                continue
    return gpus


def _parse_ram_windows():
    """Returns total system RAM in MB using Get-CimInstance (Windows 11 compatible)."""
    ps_cmd = "(Get-CimInstance -ClassName Win32_ComputerSystem).TotalPhysicalMemory"
    out = _run_cmd(f'powershell -NoProfile -Command "{ps_cmd}"', timeout=5)
    try:
        return int(out.strip()) // (1024 ** 2)
    except Exception:
        return 32768  # fallback 32GB


def _parse_npu_windows():
    """Detects NPU (AMD Ryzen AI) on Windows using Get-PnpDevice."""
    cmd = "powershell -NoProfile -Command \"Get-PnpDevice -FriendlyName '*NPU*' | Select-Object -ExpandProperty FriendlyName -First 1\""
    out = _run_cmd(cmd, timeout=5)
    if out and "NPU" in out:
        return out.strip()
    return None


def _parse_gpu_linux():
    """Parses GPU info on Linux using lspci."""
    gpus = []
    lspci = _run_cmd("lspci 2>/dev/null | grep -iE 'vga|3d|display'")
    if lspci:
        for line in lspci.splitlines():
            name = line.split(":")[-1].strip()
            if name:
                gpus.append({"name": name, "vram_bytes": 0})
    return gpus


def _parse_ram_linux():
    """Returns total system RAM in MB on Linux."""
    out = _run_cmd("grep MemTotal /proc/meminfo 2>/dev/null")
    try:
        return int(re.search(r'\d+', out).group()) // 1024
    except Exception:
        return 16384


def _classify_gpu(name, vram_bytes, total_ram_mb):
    """
    Builds a GPU info dict from raw WMI/lspci data.
    Returns a fully classified dict with vendor, is_igpu, gpu_type, vram_mb, gfx_version.
    """
    name_lower = name.lower()
    info = {
        "name":        name,
        "vram_bytes":  vram_bytes,
        "vram_mb":     vram_bytes // (1024 ** 2) if vram_bytes > 0 else 0,
        "vendor":      "unknown",
        "is_igpu":     False,
        "gpu_type":    "cpu",
        "gfx_version": None,
    }

    if "amd" in name_lower or "radeon" in name_lower:
        info["vendor"]   = "amd"
        info["gpu_type"] = "rocm"
        igpu_keywords = [
            "780m", "760m", "740m", "890m", "880m", "680m",
            "integrated", "igpu", "vega", "raphael", "phoenix",
        ]
        info["is_igpu"]     = any(k in name_lower for k in igpu_keywords)
        info["gfx_version"] = _detect_amd_gfx(name_lower)

    elif any(x in name_lower for x in ["nvidia", "geforce", "rtx", "gtx", "quadro", "tesla"]):
        info["vendor"]   = "nvidia"
        info["gpu_type"] = "cuda"

    elif "intel" in name_lower:
        info["vendor"]   = "intel"
        info["gpu_type"] = "vulkan"
        info["is_igpu"]  = True

    # iGPU with shared memory: OS reports fictitious VRAM (512MB or similar).
    # Estimate real allocated VRAM as 35% of total system RAM.
    if info["is_igpu"] and info["vram_mb"] < 8192:
        info["vram_mb"] = int(total_ram_mb * 0.35)

    return info


def detect_gpu():
    """
    FEAT-14: Detects ALL GPUs and returns a complete hardware profile.

    Profile includes:
      - Primary GPU fields (gpu_name, vendor, vram_mb, is_igpu, gpu_type, gfx_version)
      - all_gpus: list of ALL detected GPUs (iGPU + dGPU) for split-offload support
      - total_ram_mb: total system RAM
    """
    profile = {
        "gpu_name":    "Unknown",
        "vendor":      "unknown",
        "vram_mb":     8192,
        "total_ram_mb": 16384,
        "is_igpu":     False,
        "gpu_type":    "cpu",
        "gfx_version": None,
        "all_gpus":    [],          # FEAT-14: all detected GPUs
    }

    is_windows = platform.system() == "Windows"
    raw_gpus   = _parse_gpu_windows() if is_windows else _parse_gpu_linux()
    total_ram  = _parse_ram_windows() if is_windows else _parse_ram_linux()
    profile["total_ram_mb"] = total_ram

    # Classify all raw GPU entries
    classified = [_classify_gpu(g["name"], g["vram_bytes"], total_ram) for g in raw_gpus]
    profile["all_gpus"] = classified

    if not classified:
        return profile

    # Select primary GPU: prefer dGPU (non-igpu, most VRAM), then igpu
    dgpus = [g for g in classified if not g["is_igpu"]]
    igpus = [g for g in classified if g["is_igpu"]]

    primary = None
    if dgpus:
        primary = max(dgpus, key=lambda g: g["vram_mb"])
    elif igpus:
        primary = max(igpus, key=lambda g: g["vram_mb"])

    if primary:
        profile["gpu_name"]    = primary["name"]
        profile["vram_mb"]     = primary["vram_mb"]
        profile["vendor"]      = primary["vendor"]
        profile["is_igpu"]     = primary["is_igpu"]
        profile["gpu_type"]    = primary["gpu_type"]
        profile["gfx_version"] = primary["gfx_version"]

    return profile


def calculate_optimal_ctx(vram_mb, model_size_b=32, kv_quant="q4_0"):
    """
    Calculates the maximum context window that fits in available VRAM.

    KV-cache MB per token:
      FP16  (f16):  0.500 × model_size_B
      Q8_0 (q8_0): 0.250 × model_size_B  (2× reduction)
      Q4_0 (q4_0): 0.125 × model_size_B  (4× reduction)

    We allocate 45% of VRAM to KV-cache, leaving the rest for model weights + overhead.
    Floor: minimum 8192 tokens regardless of hardware.
    """
    quant_mb_per_token = {"f16": 0.500, "q8_0": 0.250, "q4_0": 0.125}
    kv_mb_per_token = quant_mb_per_token.get(kv_quant, 0.125) * model_size_b
    available_for_kv_mb = vram_mb * 0.45

    if kv_mb_per_token <= 0:
        return 8192

    ctx = int(available_for_kv_mb / kv_mb_per_token)

    # Snap to standard context sizes
    for threshold in [524288, 131072, 65536, 32768, 16384, 8192]:
        if ctx >= threshold:
            return threshold
    return 8192  # Guaranteed minimum floor


def get_full_profile():
    """
    Main entry point. Returns the complete hardware profile dict,
    including optimal context window for the currently active model.
    """
    gpu = detect_gpu()

    # Detect current model size from settings
    model_size_b = 32  # Default: 32B
    try:
        with open(os.path.join(BASE_DIR, "_settings.json"), "r", encoding="utf-8") as f:
            settings = json.load(f)
        model_name = settings.get("last_model", "").lower()
        for size_str, size_b in [
            ("70b", 70), ("72b", 72), ("32b", 32), ("30b", 30),
            ("14b", 14), ("13b", 13), ("8b", 8), ("7b", 7), ("3b", 3), ("1b", 1)
        ]:
            if size_str in model_name:
                model_size_b = size_b
                break
    except Exception:
        pass

    kv_quant    = "q4_0" if gpu["vram_mb"] < 10000 else "q8_0"
    optimal_ctx = calculate_optimal_ctx(gpu["vram_mb"], model_size_b, kv_quant)

    npu_name = _parse_npu_windows() if platform.system() == "Windows" else None

    return {
        **gpu,
        "npu_name":     npu_name,
        "model_size_b": model_size_b,
        "kv_quant":     kv_quant,
        "optimal_ctx":  optimal_ctx,
        "is_amd":       gpu["vendor"] == "amd",
        "is_nvidia":    gpu["vendor"] == "nvidia",
    }


if __name__ == "__main__":
    print("\n╔════════════════════════════════════╗")
    print("║  GRAVITY AI HARDWARE PROFILER V7.1 ║")
    print("╚════════════════════════════════════╝\n")

    p = get_full_profile()
    print(f"  GPU (Primary)  : {p['gpu_name']}")
    print(f"  Vendor         : {p['vendor'].upper()}")
    print(f"  Tipo           : {'iGPU (Integrada)' if p['is_igpu'] else 'dGPU (Dedicada)'}")
    print(f"  VRAM Estimada  : {p['vram_mb']:,} MB ({p['vram_mb']/1024:.1f} GB)")
    print(f"  RAM Total      : {p['total_ram_mb']:,} MB ({p['total_ram_mb']//1024} GB)")
    print(f"  GPU Backend    : {p['gpu_type'].upper()}")
    if p.get("gfx_version"):
        print(f"  GFX Version    : {p['gfx_version']} (ROCm compat)")
    if p.get("npu_name"):
        print(f"  NPU Acelerador : [ACTIVO] {p['npu_name']}")

    if len(p.get("all_gpus", [])) > 1:
        print(f"\n  Todas las GPUs detectadas ({len(p['all_gpus'])}):")
        for i, g in enumerate(p["all_gpus"]):
            tag = "[iGPU]" if g["is_igpu"] else "[dGPU]"
            print(f"    [{i}] {tag} {g['name']} — {g['vram_mb']:,} MB ({g['vendor'].upper()})")

    print(f"\n  Modelo ({p['model_size_b']}B)   : {p['kv_quant'].upper()} KV-Cache")
    print(f"  Contexto Óptimo : {p['optimal_ctx']:,} tokens")
    print()
