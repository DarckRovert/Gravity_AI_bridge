"""
╔══════════════════════════════════════════════════════════════╗
║     GRAVITY AI BRIDGE V10.0 — Silent Launcher                ║
║     Inicia el Bridge + Tray sin mostrar consola              ║
╚══════════════════════════════════════════════════════════════╝

Este archivo es .pyw para ejecución sin ventana de consola.
PyInstaller lo empaquetará con --noconsole.

Flujo:
  1. Verifica si ya hay una instancia corriendo (PID file)
  2. Inicia bridge_server.py como subproceso
  3. Espera a que el servidor responda en el puerto 7860
  4. Abre el Dashboard en el navegador (primer arranque o siempre)
  5. Inicia el icono de bandeja del sistema (bloqueante)
"""

import os
import sys
import time
import subprocess
import webbrowser
import threading
import atexit

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PID_FILE   = os.path.join(BASE_DIR, "_gravity_launcher.pid")
BRIDGE_PY  = os.path.join(BASE_DIR, "bridge_server.py")
DASHBOARD  = "http://127.0.0.1:7860"
PORT       = 7860
PYTHON     = sys.executable


# ── Single Instance Guard ──────────────────────────────────────────────────────

def _already_running() -> bool:
    if not os.path.exists(PID_FILE):
        return False
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        # Verificar si el proceso sigue vivo
        import psutil
        proc = psutil.Process(pid)
        if proc.is_running():
            return True
    except Exception:
        pass
    # PID file obsoleto
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
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            urllib.request.urlopen(f"{DASHBOARD}/health", timeout=1)
            return True
        except Exception:
            time.sleep(1.0)
    return False


# ── Bridge Process ────────────────────────────────────────────────────────────

_bridge_proc = None


def _start_bridge():
    global _bridge_proc
    # Si se ejecuta desde un bundle PyInstaller, el script puede estar embebido
    if getattr(sys, "frozen", False):
        # Modo empaquetado: el bridge se ejecuta como función, no como subproceso
        # Usamos threading para no bloquear el launcher
        def _run_bridge_in_thread():
            try:
                import bridge_server
                bridge_server.main()
            except Exception as e:
                pass  # Silent fail — tray indicará estado offline
        t = threading.Thread(target=_run_bridge_in_thread, daemon=True)
        t.start()
    else:
        # Modo desarrollo: subproceso separado
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW
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


# ── First Run Detection ────────────────────────────────────────────────────────

def _is_first_run() -> bool:
    marker = os.path.join(BASE_DIR, "_first_run_done")
    return not os.path.exists(marker)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Guard de instancia única
    if _already_running():
        # Ya está corriendo — sólo abrir el dashboard
        webbrowser.open(DASHBOARD)
        return

    _write_pid()
    atexit.register(_cleanup_pid)
    atexit.register(_stop_bridge)

    # Iniciar el servidor bridge
    _start_bridge()

    # Esperar a que el bridge esté listo
    online = _wait_for_bridge(timeout=90.0)

    # Abrir dashboard en el navegador
    if online or _is_first_run():
        webbrowser.open(DASHBOARD)

    # Iniciar el icono de bandeja (bloqueante)
    try:
        from gravity_tray import run_tray
        run_tray()
    except Exception:
        # Si pystray/Pillow no están disponibles, esperar indefinidamente
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
