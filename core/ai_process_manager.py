import os
import subprocess
import yaml
import time
import logging
import threading
from typing import Dict, Any, Optional

# psutil es opcional — si no está instalado el motor de stop funciona en modo reducido
try:
    import psutil
    _PSUTIL_OK = True
except ImportError:
    psutil = None
    _PSUTIL_OK = False

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE  = os.path.join(BASE_DIR, "config.yaml")
_config_lock = threading.RLock()

log = logging.getLogger("gravity.ai_process_manager")


def get_config() -> Dict[str, Any]:
    """Reads configuration safely under reentrant lock."""
    with _config_lock:
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}


def save_config(data: Dict[str, Any]) -> None:
    """Writes configuration safely under reentrant lock."""
    with _config_lock:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        except Exception:
            pass


def discover_apps() -> Dict[str, str]:
    """Busca rutas de IAs conocidas en el sistema y las guarda en config.yaml"""
    log.info("[AI Process Manager] Buscando motores IA locales...")

    localappdata = os.environ.get("LOCALAPPDATA", "")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    found_paths: Dict[str, str] = {}

    # 1. LM Studio
    lm_studio = os.path.join(localappdata, "Programs", "LM Studio", "LM Studio.exe")
    if os.path.exists(lm_studio):
        found_paths["LM Studio"] = lm_studio

    # 2. Ollama
    ollama = os.path.join(localappdata, "Programs", "Ollama", "ollama app.exe")
    if os.path.exists(ollama):
        found_paths["Ollama"] = ollama

    # 3. Fooocus
    fooocus = os.path.join(base_dir, "_integrations", "Fooocus", "run.bat")
    if os.path.exists(fooocus):
        found_paths["Fooocus"] = fooocus

    # 4. Jan
    jan = os.path.join(localappdata, "Programs", "Jan", "Jan.exe")
    if os.path.exists(jan):
        found_paths["Jan AI"] = jan

    # 5. ComfyUI
    comfyui = os.path.join(base_dir, "_integrations", "ComfyUI_windows_portable", "run_amd_gpu.bat")
    if os.path.exists(comfyui):
        found_paths["ComfyUI"] = comfyui

    # 6. V2V Engine
    v2v = os.path.join(base_dir, "_integrations", "v2v_engine", "run_v2v.bat")
    if os.path.exists(v2v):
        found_paths["V2V Engine"] = v2v

    if not found_paths:
        return {}

    c = get_config()
    if "ai_engines" not in c:
        c["ai_engines"] = {}

    for k, v in found_paths.items():
        if k not in c["ai_engines"] or not c["ai_engines"][k]:
            c["ai_engines"][k] = v
            log.info(f"[AI Process Manager] Autodescubierto: {k} -> {v}")

    save_config(c)
    return found_paths


def get_engine_path(provider_name: str) -> Optional[str]:
    """Retrieves the executable path for the requested AI provider."""
    c = get_config()
    return c.get("ai_engines", {}).get(provider_name)


def is_engine_running(provider_name: str) -> bool:
    """Verifica si el proceso del motor ya está corriendo usando psutil."""
    if not _PSUTIL_OK:
        return False
        
    pn = provider_name.lower()
    targets = []
    if "lm studio" in pn:
        targets = ["LM Studio.exe", "lmstudioworker.exe"]
    elif "ollama" in pn:
        targets = ["ollama.exe", "ollama app.exe", "ollama_llama_server.exe"]
    elif "jan" in pn:
        targets = ["Jan.exe"]
        
    for proc in psutil.process_iter(['name', 'cmdline', 'cwd']):
        try:
            name = proc.info.get('name', '')
            if not name: continue
            
            p_cwd   = proc.info.get('cwd', '') or ''
            cmdline = " ".join(proc.info.get('cmdline', []) or [])
            
            if "fooocus" in pn and "python.exe" in name.lower():
                if "launch.py" in cmdline or "Fooocus" in p_cwd:
                    return True
            if "comfyui" in pn and "python.exe" in name.lower():
                if "comfyui\\main.py" in cmdline.lower() or "comfyui" in p_cwd.lower():
                    return True
            if "v2v" in pn and "python.exe" in name.lower():
                if "v2v_pipeline.py" in cmdline.lower() or "v2v_server.py" in cmdline.lower() or "v2v_engine" in p_cwd.lower():
                    return True
                    
            if targets and any(t.lower() in name.lower() for t in targets):
                return True
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    return False


def start_engine(provider_name: str) -> Dict[str, Any]:
    """Inicia silenciosamente el motor si se conoce su ruta."""
    if is_engine_running(provider_name):
        log.info(f"[AI Process Manager] {provider_name} ya está en ejecución a nivel proceso. Evitando duplicados.")
        return {"success": True, "message": f"{provider_name} ya estaba corriendo."}
        
    path = get_engine_path(provider_name)
    if not path or not os.path.exists(path):
        return {
            "success": False,
            "error": f"Ruta desconocida para {provider_name}. "
                     "Configura en config.yaml u ocurrio fallo de descubrimiento.",
        }

    try:
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_CONSOLE = 0x00000010
        CREATE_NO_WINDOW = 0x08000000
        
        # Para V2V, Fooocus o ComfyUI, necesitamos consola visible para debug y UI
        if "v2v" in provider_name.lower() or "fooocus" in provider_name.lower() or "comfyui" in provider_name.lower():
            proc_flags = CREATE_NEW_CONSOLE
        else:
            proc_flags = DETACHED_PROCESS | CREATE_NO_WINDOW
            
        env = os.environ.copy()

        if path.endswith(".bat"):
            subprocess.Popen(
                ["cmd.exe", "/c", path],
                creationflags=proc_flags,
                cwd=os.path.dirname(path),
                env=env,
                close_fds=True,
            )
        else:
            subprocess.Popen(
                [path],
                creationflags=proc_flags,
                cwd=os.path.dirname(path),
                env=env,
                close_fds=True,
            )
        return {"success": True, "message": f"{provider_name} iniciado en background."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def stop_engine(provider_name: str) -> Dict[str, Any]:
    """Mata el proceso nativo buscando ejecutables coincidentes."""
    if not _PSUTIL_OK:
        return {"success": False, "error": "psutil no instalado. Ejecuta: pip install psutil"}

    targets = []
    pn = provider_name.lower()

    if "lm studio" in pn:
        targets = ["LM Studio.exe", "lmstudioworker.exe"]
    elif "ollama" in pn:
        targets = ["ollama.exe", "ollama app.exe", "ollama_llama_server.exe"]
    elif "jan" in pn:
        targets = ["Jan.exe"]
    elif "fooocus" in pn:
        targets = []  # Evitamos targets genéricos para no matar procesos del bridge
    elif "comfyui" in pn:
        targets = []  # Igual que Fooocus
    elif "v2v" in pn:
        targets = []  # V2V
    else:
        return {"success": False, "error": "Firma del motor no registrada aún. No puedo apagar."}

    killed = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
        try:
            name = proc.info.get('name', '')
            if not name:
                continue

            p_cwd   = proc.info.get('cwd', '') or ''
            cmdline = " ".join(proc.info.get('cmdline', []) or [])

            # Límite riguroso para Fooocus (no matar al servidor bridge u otros pythons)
            if "fooocus" in pn and "python.exe" in name.lower():
                if "launch.py" in cmdline or "Fooocus" in p_cwd:
                    proc.kill()
                    killed += 1
                    continue

            # Límite riguroso para ComfyUI
            if "comfyui" in pn and "python.exe" in name.lower():
                if "comfyui\\main.py" in cmdline.lower() or "comfyui" in p_cwd.lower():
                    proc.kill()
                    killed += 1
                    continue

            # Límite riguroso para V2V
            if "v2v" in pn and "python.exe" in name.lower():
                if "v2v_pipeline.py" in cmdline.lower() or "v2v_server.py" in cmdline.lower() or "v2v_engine" in p_cwd.lower():
                    proc.kill()
                    killed += 1
                    continue

            if any(t.lower() in name.lower() for t in targets):
                proc.kill()
                killed += 1
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue

    if killed > 0:
        return {"success": True, "message": f"{provider_name} detenido ({killed} procesos cerrados)."}
    else:
        return {"success": False, "error": "No se encontró el proceso en ejecución local."}
