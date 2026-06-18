"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — PLAYWRIGHT WORKER (Proceso Hijo Aislado)                       ║
║  Ejecuta operaciones de Playwright en un subproceso separado del servidor.   ║
║  Si Playwright crashea (Segfault, OOM, timeout), el servidor principal       ║
║  sigue vivo — solo muere este proceso hijo.                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

ARQUITECTURA:
  bridge_server.py  ──► _playwright_worker.py (subproceso hijo)
       ▲                        │
       └── resultado JSON ◄─────┘  (stdout del subproceso)

Este módulo puede ser:
  1. Importado: run_isolated(task_name, **kwargs) → dict
  2. Ejecutado directamente: python _playwright_worker.py <task_json>
"""

import os
import sys
import json
import subprocess
import tempfile
import time
from typing import Any, Dict

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_EXE = sys.executable

# Timeout por defecto por tarea (segundos)
TASK_TIMEOUTS = {
    "upload_tiktok":    300,   # 5 minutos
    "upload_instagram": 300,
    "login_tiktok":     600,   # 10 minutos (login manual)
    "login_instagram":  600,
    "default":          180,
}


def run_isolated(task_name: str, timeout: int = None, **kwargs) -> Dict[str, Any]:
    """
    Ejecuta una tarea de Playwright en un subproceso hijo aislado.

    El subproceso recibe los argumentos via stdin como JSON,
    ejecuta la tarea y escribe el resultado en stdout como JSON.

    Si el subproceso excede el timeout o crashea, retorna error
    sin afectar al servidor principal.

    Args:
        task_name: Nombre de la tarea (ej. "upload_tiktok")
        timeout:   Timeout en segundos (usa TASK_TIMEOUTS si None)
        **kwargs:  Argumentos de la tarea

    Returns:
        Dict con {"ok": bool, ...datos del resultado o "error": str}
    """
    if timeout is None:
        timeout = TASK_TIMEOUTS.get(task_name, TASK_TIMEOUTS["default"])

    payload = json.dumps({"task": task_name, "args": kwargs})
    worker_script = os.path.abspath(__file__)

    try:
        proc = subprocess.Popen(
            [PYTHON_EXE, worker_script],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=BASE_DIR,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )

        try:
            stdout, stderr = proc.communicate(
                input=payload.encode("utf-8"),
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()  # flush buffers
            return {
                "ok": False,
                "error": f"Playwright worker timeout tras {timeout}s",
                "task": task_name,
            }

        if proc.returncode != 0:
            err_msg = stderr.decode("utf-8", errors="replace").strip()[-500:]
            return {
                "ok": False,
                "error": f"Worker crashed (exit={proc.returncode}): {err_msg}",
                "task": task_name,
            }

        # Parsear resultado JSON del stdout del subproceso
        try:
            output = stdout.decode("utf-8", errors="replace").strip()
            # Tomar solo la última línea JSON (puede haber logs de Playwright antes)
            for line in reversed(output.splitlines()):
                line = line.strip()
                if line.startswith("{"):
                    return json.loads(line)
            return {"ok": False, "error": "Worker no retornó JSON válido", "raw": output[-200:]}
        except json.JSONDecodeError as e:
            return {"ok": False, "error": f"JSON parse error: {e}", "raw": stdout.decode(errors="replace")[-200:]}

    except FileNotFoundError:
        return {"ok": False, "error": "Python executable no encontrado"}
    except Exception as e:
        return {"ok": False, "error": f"Error lanzando worker: {e}"}


# ── Implementación de tareas (corre en el subproceso hijo) ────────────────────

def _task_upload_tiktok(args: Dict) -> Dict:
    """Sube un video a TikTok usando StealthUploader."""
    video_path = args.get("video_path", "")
    caption    = args.get("caption", "")
    if not video_path or not os.path.exists(video_path):
        return {"ok": False, "error": f"Archivo no encontrado: {video_path}"}

    sys.path.insert(0, BASE_DIR)
    from core.stealth_uploader import StealthUploader
    uploader = StealthUploader()
    return uploader.upload_to_tiktok(video_path, caption)


def _task_upload_instagram(args: Dict) -> Dict:
    """Sube un video a Instagram usando StealthUploader."""
    video_path = args.get("video_path", "")
    caption    = args.get("caption", "")
    if not video_path or not os.path.exists(video_path):
        return {"ok": False, "error": f"Archivo no encontrado: {video_path}"}

    sys.path.insert(0, BASE_DIR)
    from core.stealth_uploader import StealthUploader
    uploader = StealthUploader()
    return uploader.upload_to_instagram(video_path, caption)


def _task_login_tiktok(args: Dict) -> Dict:
    """Abre el navegador para login manual en TikTok/Instagram."""
    sys.path.insert(0, BASE_DIR)
    from core.stealth_uploader import start_login
    start_login()
    return {"ok": True, "message": "Sesión guardada correctamente"}


TASK_HANDLERS = {
    "upload_tiktok":    _task_upload_tiktok,
    "upload_instagram": _task_upload_instagram,
    "login_tiktok":     _task_login_tiktok,
}


def _worker_main():
    """
    Entry point del proceso hijo.
    Lee el payload desde stdin, ejecuta la tarea, escribe el resultado en stdout.
    """
    try:
        payload_raw = sys.stdin.read()
        payload     = json.loads(payload_raw)
        task_name   = payload.get("task")
        task_args   = payload.get("args", {})

        handler = TASK_HANDLERS.get(task_name)
        if not handler:
            result = {"ok": False, "error": f"Tarea desconocida: {task_name}"}
        else:
            result = handler(task_args)

        # Escribir resultado como última línea JSON en stdout
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0)

    except Exception as e:
        print(json.dumps({"ok": False, "error": f"Worker error: {e}"}))
        sys.exit(1)


if __name__ == "__main__":
    _worker_main()
