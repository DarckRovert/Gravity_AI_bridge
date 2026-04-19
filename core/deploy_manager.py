"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         GRAVITY AI — DEPLOY MANAGER V9.4                                     ║
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
from datetime import datetime
from typing import Optional

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_FILE = os.path.join(BASE_DIR, "_settings.json")

# ── Estado ─────────────────────────────────────────────────────────────────────

_state: dict = {
    "status":     "idle",        # idle | building | deploying | done | failed
    "last_run":   None,
    "project":    None,
    "log":        [],
    "netlify_url": None,
    "error":      None,
}
_lock    = threading.Lock()
_running = False


# ── Detección de Herramientas ──────────────────────────────────────────────────

def _which(cmd: str) -> Optional[str]:
    """Busca un ejecutable en el PATH del sistema."""
    try:
        result = subprocess.run(
            ["where" if os.name == "nt" else "which", cmd],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip().splitlines()[0]
    except Exception:
        pass
    return None


def check_tools() -> dict:
    """Verifica disponibilidad de npm y netlify CLI."""
    return {
        "npm":     _which("npm") is not None,
        "netlify": _which("netlify") is not None,
        "node":    _which("node") is not None,
    }


def get_project_path() -> str:
    """Lee la ruta del proyecto activo desde _settings.json."""
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("active_project_path")
    except Exception:
        return None


def detect_output_dir(project_path: str) -> str:
    """
    Detecta dinámicamente la carpeta de build del proyecto.
    Estrategia:
      1. Leer `package.json` para detectar framework (next, vite, react-scripts).
      2. Para Vite: buscar `outDir` en vite.config.js / vite.config.ts con regex.
      3. Para Next.js: verificar si `next.config.*` tiene `output: 'export'` (→ /out).
      4. Fallback ordenado: /out → /dist → /build → project_path.
    """
    import re

    def _safe_read(path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception:
            return ""

    # 1. Leer package.json
    pkg_path  = os.path.join(project_path, "package.json")
    pkg_text  = _safe_read(pkg_path)
    framework = "unknown"
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
            cfg_text = _safe_read(os.path.join(project_path, cfg_name))
            if cfg_text:
                match = re.search(r'outDir\s*:\s*[\'"]([^\'"]+)[\'"]', cfg_text)
                if match:
                    custom_out = os.path.join(project_path, match.group(1))
                    if os.path.isdir(custom_out):
                        return custom_out
        # Vite default: /dist
        dist = os.path.join(project_path, "dist")
        if os.path.isdir(dist):
            return dist

    # 3. Next.js
    if framework == "next":
        for cfg_name in ("next.config.js", "next.config.ts", "next.config.mjs"):
            cfg_text = _safe_read(os.path.join(project_path, cfg_name))
            if "output" in cfg_text and "export" in cfg_text:
                # next export mode → /out
                out = os.path.join(project_path, "out")
                if os.path.isdir(out):
                    return out
        # Next.js sin export estático → /.next/standalone o /out
        out = os.path.join(project_path, "out")
        if os.path.isdir(out):
            return out

    # 4. CRA y fallback genérico
    for candidate in ("build", "out", "dist"):
        path = os.path.join(project_path, candidate)
        if os.path.isdir(path):
            return path

    return project_path  # Último fallback absoluto


# ── Pipeline ───────────────────────────────────────────────────────────────────

def _log(msg: str) -> None:
    ts    = datetime.utcnow().strftime("%H:%M:%S")
    entry = f"[{ts}] {msg}"
    with _lock:
        _state["log"].append(entry)
        # Mantener solo las últimas 200 líneas
        if len(_state["log"]) > 200:
            _state["log"] = _state["log"][-200:]


def _run_step(cmd: list[str], cwd: str, timeout: int = 300) -> tuple[bool, str]:
    """Ejecuta un comando y retorna (éxito, salida)."""
    try:
        _log(f"$ {' '.join(cmd)}")
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        output_lines = []
        for line in iter(proc.stdout.readline, ""):
            if not line:
                break
            cleaned = line.rstrip()
            output_lines.append(cleaned)
            _log(cleaned)

        proc.wait(timeout=timeout)
        output = "\n".join(output_lines)

        if proc.returncode != 0:
            return False, output
        return True, output

    except subprocess.TimeoutExpired:
        proc.kill()
        return False, "TIMEOUT: proceso cancelado"
    except Exception as e:
        return False, str(e)


def _pipeline(project_path: str) -> None:
    """Ejecuta el pipeline completo de build + deploy en background."""
    global _running

    with _lock:
        _state["status"]     = "building"
        _state["log"]        = []
        _state["netlify_url"] = None
        _state["error"]      = None
        _state["last_run"]   = datetime.utcnow().isoformat() + "Z"
        _state["project"]    = project_path

    _log(f"Iniciando pipeline para: {project_path}")

    tools = check_tools()
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
    out_dir = detect_output_dir(project_path)
    _log(f"Carpeta de build detectada: {out_dir}")
    ok, output = _run_step(
        ["netlify", "deploy", "--prod", f"--dir={out_dir}"],
        cwd=project_path,
        timeout=120
    )

    # Extraer URL de Netlify del output
    netlify_url = None
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

def start_deploy(project_path: Optional[str] = None) -> dict:
    """
    Inicia el pipeline de build + deploy en background.
    Retorna el estado inicial inmediatamente.
    """
    global _running

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

    with _lock:
        if _running:
            return {"started": False, "reason": "La ejecución ha sido interceptada por otro hilo en la fracción de segundo."}
        _running = True
        t = threading.Thread(
            target=_pipeline,
            args=(project_path,),
            name="GravityDeployPipeline",
            daemon=True,
        )
        t.start()

    return {"started": True, "project": project_path}


def get_status() -> dict:
    """Retorna el estado actual del último deploy."""
    with _lock:
        return {
            **_state,
            "tools": check_tools(),
            "running": _running,
        }
