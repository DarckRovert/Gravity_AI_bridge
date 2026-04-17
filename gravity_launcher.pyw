"""
╔══════════════════════════════════════════════════════════════╗
║     GRAVITY AI BRIDGE V10.0 — Silent Launcher                ║
║     Inicia el Bridge + Tray sin mostrar consola              ║
╚══════════════════════════════════════════════════════════════╝

Flujo en modo instalado (frozen exe):
  1. Si el argumento --server-only está presente → corre bridge_server directamente
     (Este es el subproceso servidor, sin UI ni tray)
  2. Sin ese argumento → modo launcher:
     a. Verifica instancia única (PID file)
     b. Lanza ESTE MISMO EXE con --server-only como subproceso
     c. Espera health check en el puerto 7860 (máx. 90s)
     d. Abre el Dashboard en el navegador cuando el bridge responde
     e. Inicia el icono de bandeja del sistema (bloqueante)

Flujo en modo desarrollo (.pyw directo):
  - Lanza bridge_server.py como subproceso separado con python
"""

import os
import sys
import time
import subprocess
import webbrowser
import atexit

# ── Rutas base ────────────────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    # Ejecutable compilado — usar directorio del .exe instalado
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
    EXE_PATH = os.path.abspath(sys.executable)
else:
    # Modo desarrollo — directorio del script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXE_PATH = None

PID_FILE   = os.path.join(BASE_DIR, "_gravity_launcher.pid")
BRIDGE_PY  = os.path.join(BASE_DIR, "bridge_server.py")
LOG_FILE   = os.path.join(BASE_DIR, "_gravity_server.log")
DASHBOARD  = "http://127.0.0.1:7860"
PORT       = 7860
PYTHON     = sys.executable


# ── Modo servidor (subproceso) ──────────────────────────────────────────────────
# Cuando el exe se lanza con --server-only, ejecuta bridge_server directamente
# y escribe los errores a un log en el directorio de instalación.

def _run_as_server():
    """Entry point cuando se ejecuta con --server-only."""
    log_path = LOG_FILE
    try:
        # Calcular _MEIPASS del SUBPROCESO actual (no del launcher padre)
        meipass = getattr(sys, "_MEIPASS", None)

        # El directorio del exe instalado
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))

        # Cambiar al directorio del exe para que config.yaml y web/ sean accesibles
        os.chdir(exe_dir)

        # Construir sys.path con todas las rutas necesarias
        paths_to_add = [exe_dir]
        if meipass:
            paths_to_add.insert(0, meipass)

        for p in paths_to_add:
            if p not in sys.path:
                sys.path.insert(0, p)

        # Redirigir stdout/stderr al log
        log_f = open(log_path, "w", encoding="utf-8", errors="replace")
        sys.stdout = log_f
        sys.stderr = log_f

        print(f"[GRAVITY SERVER] exe_dir:  {exe_dir}")
        print(f"[GRAVITY SERVER] meipass:  {meipass}")
        print(f"[GRAVITY SERVER] sys.path: {sys.path[:6]}")
        print(f"[GRAVITY SERVER] config.yaml: {os.path.exists(os.path.join(exe_dir, 'config.yaml'))}")
        print(f"[GRAVITY SERVER] web/dashboard.html: {os.path.exists(os.path.join(exe_dir, 'web', 'dashboard.html'))}")
        log_f.flush()

        # Importar y ejecutar bridge_server
        # Primero intentar import normal (si está en sys.path via _MEIPASS o exe_dir)
        # Si falla, cargar el archivo directamente con importlib
        try:
            import bridge_server as _bs
            print("[GRAVITY SERVER] bridge_server importado via sys.path")
        except ImportError:
            # Último recurso: cargar desde ruta absoluta
            import importlib.util
            bs_path = os.path.join(meipass or exe_dir, "bridge_server.py")
            if not os.path.exists(bs_path):
                bs_path = os.path.join(exe_dir, "bridge_server.py")
            print(f"[GRAVITY SERVER] Cargando bridge_server desde: {bs_path}")
            spec = importlib.util.spec_from_file_location("bridge_server", bs_path)
            _bs = importlib.util.module_from_spec(spec)
            sys.modules["bridge_server"] = _bs
            spec.loader.exec_module(_bs)

        log_f.flush()
        _bs.run_server()

    except Exception:
        import traceback
        try:
            with open(log_path, "a", encoding="utf-8", errors="replace") as f:
                f.write(f"\n[GRAVITY SERVER] CRASH:\n{traceback.format_exc()}\n")
        except Exception:
            pass
        sys.exit(1)


# ── Single Instance Guard ─────────────────────────────────────────────────────

def _already_running() -> bool:
    if not os.path.exists(PID_FILE):
        return False
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        import psutil
        proc = psutil.Process(pid)
        if proc.is_running():
            return True
    except Exception:
        pass
    try:
        os.remove(PID_FILE)
    except Exception:
        pass
    return False


def _write_pid():
    try:
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
    except Exception:
        pass


def _cleanup_pid():
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except Exception:
        pass


# ── Bridge Health Check ────────────────────────────────────────────────────────

def _wait_for_bridge(timeout: float = 90.0) -> bool:
    """Espera hasta que el bridge responda en el puerto configurado."""
    import urllib.request
    import urllib.error
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            urllib.request.urlopen(f"{DASHBOARD}/health", timeout=2)
            return True
        except urllib.error.HTTPError:
            # El servidor responde (aunque con error HTTP) → está vivo
            return True
        except Exception:
            time.sleep(1.0)
    return False


# ── Bridge Process ────────────────────────────────────────────────────────────

_bridge_proc = None


def _start_bridge():
    global _bridge_proc
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

    if getattr(sys, "frozen", False):
        # Modo instalado: lanzar ESTE MISMO exe con --server-only
        # El subproceso del servidor corre bridge_server.run_server() con log en disco
        _bridge_proc = subprocess.Popen(
            [EXE_PATH, "--server-only"],
            cwd=BASE_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )
    else:
        # Modo desarrollo: lanzar bridge_server.py con python
        _bridge_proc = subprocess.Popen(
            [PYTHON, BRIDGE_PY],
            cwd=BASE_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )


def _stop_bridge():
    global _bridge_proc
    if _bridge_proc and _bridge_proc.poll() is None:
        try:
            _bridge_proc.terminate()
            _bridge_proc.wait(timeout=5)
        except Exception:
            try:
                _bridge_proc.kill()
            except Exception:
                pass


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Guard de instancia única
    if _already_running():
        webbrowser.open(DASHBOARD)
        return

    _write_pid()
    atexit.register(_cleanup_pid)
    atexit.register(_stop_bridge)

    # Limpiar log anterior
    try:
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
    except Exception:
        pass

    # Iniciar servidor bridge
    _start_bridge()

    # Esperar a que el bridge esté listo
    online = _wait_for_bridge(timeout=90.0)

    if online:
        webbrowser.open(DASHBOARD)

    # Iniciar el icono de bandeja del sistema (bloqueante)
    try:
        from gravity_tray import run_tray
        run_tray()
    except Exception:
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            pass


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--server-only" in sys.argv:
        _run_as_server()
    else:
        main()
