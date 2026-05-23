"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         GRAVITY AI — DEPLOY MANAGER V15.1 PRO                                     ║
║         Pipeline automatizado: Build → Deploy a Netlify                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

Detecta el proyecto activo desde _settings.json y ejecuta:
  1. npm run build
  2. netlify deploy --prod --dir=out

Endpoints integrados en bridge_server:
  POST /v1/deploy         — Inicia el pipeline
  GET  /v1/deploy/status  — Estado del último deploy
"""

import os
import json
import subprocess
import threading
import time
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_FILE: str = os.path.join(BASE_DIR, "_settings.json")

# ── Estado ─────────────────────────────────────────────────────────────────────

_state: Dict[str, Any] = {
    "status":     "idle",        # idle | building | deploying | done | failed
    "last_run":   None,
    "project":    None,
    "log":        [],
    "netlify_url": None,
    "error":      None,
}
_lock: threading.RLock = threading.RLock()
_running: bool = False


# ── Detección de Herramientas ──────────────────────────────────────────────────

def _which(cmd: str) -> Optional[str]:
    """
    Busca un ejecutable en el PATH del sistema de forma portable y segura.
    """
    try:
        args: Dict[str, Any] = {"capture_output": True, "text": True, "timeout": 5}
        if os.name == "nt":
            args["creationflags"] = subprocess.CREATE_NO_WINDOW
        
        result = subprocess.run(
            ["where" if os.name == "nt" else "which", cmd],
            **args
        )
        if result.returncode == 0:
            return result.stdout.strip().splitlines()[0]
    except Exception:
        pass
    return None


def check_tools() -> Dict[str, bool]:
    """
    Verifica la disponibilidad de npm, netlify CLI y node en el entorno.
    """
    return {
        "npm":     _which("npm") is not None,
        "netlify": _which("netlify") is not None,
        "node":    _which("node") is not None,
    }


def get_project_path() -> Optional[str]:
    """
    Lee la ruta del proyecto activo desde _settings.json de forma segura y thread-safe.
    """
    with _lock:
        for attempt in range(5):
            try:
                if os.path.isfile(SETTINGS_FILE):
                    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                        data: Dict[str, Any] = json.load(f)
                    return data.get("active_project_path")
                return None
            except (PermissionError, json.JSONDecodeError):
                if attempt == 4:
                    return None
                time.sleep(0.05 * (2 ** attempt))
            except Exception:
                return None
        return None


def detect_output_dir(project_path: str) -> str:
    """
    Detecta dinámicamente la carpeta de build del proyecto de forma thread-safe.
    Estrategia:
      1. Leer package.json para detectar framework (next, vite, react-scripts).
      2. Para Vite: buscar outDir en vite.config.js / vite.config.ts con regex.
      3. Para Next.js: verificar si next.config.* tiene output: 'export' (→ /out).
      4. Fallback ordenado: /out → /dist → /build → project_path.
    """
    import re

    def _safe_read(path: str) -> str:
        for attempt in range(5):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
            except PermissionError:
                time.sleep(0.05 * (2 ** attempt))
            except Exception:
                return ""
        return ""

    # 1. Leer package.json
    pkg_path: str = os.path.join(project_path, "package.json")
    pkg_text: str = _safe_read(pkg_path)
    framework: str = "unknown"
    try:
        pkg = json.loads(pkg_text)
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        if "next" in deps:
            framework = "next"
        elif "vite" in deps:
            framework = "vite"
        elif "react-scripts" in deps:
            framework = "cra"  # Create React App
    except Exception:
        pass

    # 2. Vite: leer outDir del config
    if framework == "vite":
        for cfg_name in ("vite.config.ts", "vite.config.js", "vite.config.mjs"):
            cfg_text: str = _safe_read(os.path.join(project_path, cfg_name))
            if cfg_text:
                match = re.search(r'outDir\s*:\s*[\'"]([^\'"]+)[\'"]', cfg_text)
                if match:
                    custom_out: str = os.path.join(project_path, match.group(1))
                    if os.path.isdir(custom_out):
                        return custom_out
        # Vite default: /dist
        dist: str = os.path.join(project_path, "dist")
        if os.path.isdir(dist):
            return dist

    # 3. Next.js
    if framework == "next":
        for cfg_name in ("next.config.js", "next.config.ts", "next.config.mjs"):
            cfg_text: str = _safe_read(os.path.join(project_path, cfg_name))
            if "output" in cfg_text and "export" in cfg_text:
                # next export mode → /out
                out: str = os.path.join(project_path, "out")
                if os.path.isdir(out):
                    return out
        # Next.js sin export estático → /.next/standalone o /out
        out: str = os.path.join(project_path, "out")
        if os.path.isdir(out):
            return out

    # 4. CRA y fallback genérico
    for candidate in ("build", "out", "dist"):
        path: str = os.path.join(project_path, candidate)
        if os.path.isdir(path):
            return path

    return project_path  # Último fallback absoluto



# ── Pipeline ───────────────────────────────────────────────────────────────────

def _log(msg: str) -> None:
    """
    Agrega un registro cronológico al log de despliegue de manera thread-safe.
    """
    ts: str = datetime.now(timezone.utc).strftime("%H:%M:%S")
    entry: str = f"[{ts}] {msg}"
    with _lock:
        _state["log"].append(entry)
        if len(_state["log"]) > 200:
            _state["log"] = _state["log"][-200:]


def _run_step(cmd: List[str], cwd: str, timeout: int = 300) -> tuple[bool, str]:
    """
    Ejecuta un comando del pipeline en un subproceso portable y seguro.
    """
    try:
        _log(f"$ {' '.join(cmd)}")
        
        kwargs: Dict[str, Any] = {
            "cwd": cwd,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
        }
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            
        proc = subprocess.Popen(cmd, **kwargs)
        
        output_lines: List[str] = []
        # Leer salida en tiempo real
        if proc.stdout:
            for line in iter(proc.stdout.readline, ""):
                if not line:
                    break
                cleaned: str = line.rstrip()
                output_lines.append(cleaned)
                _log(cleaned)

        proc.wait(timeout=timeout)
        output: str = "\n".join(output_lines)

        if proc.returncode != 0:
            return False, output
        return True, output

    except subprocess.TimeoutExpired:
        try:
            proc.kill()
        except Exception:
            pass
        return False, "TIMEOUT: proceso cancelado"
    except Exception as e:
        return False, str(e)


def _pipeline(project_path: str) -> None:
    """
    Ejecuta el pipeline de compilación y despliegue en segundo plano con seguridad multihilo.
    """
    global _running

    with _lock:
        _state["status"]     = "building"
        _state["log"]        = []
        _state["netlify_url"] = None
        _state["error"]      = None
        _state["last_run"]   = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        _state["project"]    = project_path

    _log(f"Iniciando pipeline para: {project_path}")

    tools: Dict[str, bool] = check_tools()
    if not tools["npm"]:
        with _lock:
            _state["status"] = "failed"
            _state["error"]  = "npm no encontrado en el PATH del sistema."
        _running = False
        return

    # ── Paso 1: Build ──────────────────────────────────────────────────────────
    _log("=== PASO 1: npm run build ===")
    ok, output = _run_step(["npm", "run", "build"], cwd=project_path, timeout=300)

    if not ok:
        with _lock:
            _state["status"] = "failed"
            _state["error"]  = "Build fallido. Revisa el log."
        _running = False
        return

    _log("Build completado con éxito.")

    # ── Paso 2: Deploy ─────────────────────────────────────────────────────────
    if not tools["netlify"]:
        with _lock:
            _state["status"]     = "done"
            _state["netlify_url"] = None
            _state["error"]      = "netlify CLI no instalado. Build listo pero no desplegado."
        _running = False
        return

    with _lock:
        _state["status"] = "deploying"

    # Detectar carpeta de salida dinámicamente
    out_dir: str = detect_output_dir(project_path)
    _log(f"Carpeta de build detectada: {out_dir}")
    ok, output = _run_step(
        ["netlify", "deploy", "--prod", f"--dir={out_dir}"],
        cwd=project_path,
        timeout=120
    )

    # Extraer URL de Netlify del output
    netlify_url: Optional[str] = None
    for line in output.splitlines():
        if "netlify.app" in line or "Website URL" in line:
            parts = line.split()
            for part in parts:
                if "https://" in part and "netlify" in part:
                    netlify_url = part.strip()
                    break

    with _lock:
        if ok:
            _state["status"]     = "done"
            _state["netlify_url"] = netlify_url
        else:
            _state["status"] = "failed"
            _state["error"]  = "Deploy fallido. Revisa el log."

    _running = False


# ── API Pública ────────────────────────────────────────────────────────────────

def start_deploy(project_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Inicia el pipeline de compilación y despliegue en segundo plano.
    """
    global _running

    with _lock:
        if _running:
            return {"started": False, "reason": "Ya hay un pipeline en ejecución."}

        if project_path is None:
            project_path = get_project_path()

        if not project_path or not os.path.isdir(project_path):
            return {
                "started": False,
                "reason": f"Ruta de proyecto inválida o no configurada: {project_path}. "
                          "Configura 'active_project_path' en _settings.json."
            }

        _running = True
        t: threading.Thread = threading.Thread(
            target=_pipeline,
            args=(project_path,),
            name="GravityDeployPipeline",
            daemon=True,
        )
        t.start()

    return {"started": True, "project": project_path}


def get_status() -> Dict[str, Any]:
    """
    Retorna el estado detallado del último despliegue.
    """
    with _lock:
        return {
            **_state,
            "tools": check_tools(),
            "running": _running,
        }

