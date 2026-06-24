"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — WINDOWS SERVICE MANAGER                                        ║
║  Registra, inicia, detiene y desinstala Gravity como servicio de Windows     ║
║  Usa pywin32 nativo — sin dependencias externas.                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

USO:
    python gravity_service.py install    → Instalar servicio
    python gravity_service.py start      → Iniciar servicio
    python gravity_service.py stop       → Detener servicio
    python gravity_service.py restart    → Reiniciar servicio
    python gravity_service.py remove     → Desinstalar servicio
    python gravity_service.py status     → Ver estado
    python gravity_service.py debug      → Correr en primer plano (sin servicio)
"""

import os
import sys
import time
import subprocess
import ctypes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_NAME = "GravityAI"
SERVICE_DISPLAY = "Gravity AI Bridge Server"
SERVICE_DESC = (
    "Gravity AI — La primera empresa peruana autogestionada por IA. "
    "y motor de autonomía OODA."
)
# Cuando corre como servicio, sys.executable es pythonservice.exe. Forzamos a que use python.exe real.
PYTHON_EXE = os.path.join(os.path.dirname(sys.executable), "python.exe")
if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = "python.exe"  # Fallback a PATH

BRIDGE_SCRIPT = os.path.join(BASE_DIR, "bridge_server.py")
LOG_DIR = os.path.join(BASE_DIR, "logs")


def _is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def _require_admin():
    if not _is_admin():
        print("[!] Se requieren permisos de Administrador.")
        print("    Ejecuta esta terminal como Administrador e intenta de nuevo.")
        sys.exit(1)


# ── Implementación del Servicio Windows con pywin32 ───────────────────────────

try:
    import win32service
    import win32serviceutil
    import win32event
    import servicemanager
    import socket

    class GravityWindowsService(win32serviceutil.ServiceFramework):
        """
        Servicio de Windows que envuelve bridge_server.py.
        Al iniciar, levanta bridge_server en un subproceso hijo.
        Si el subproceso muere inesperadamente, el servicio lo reinicia.
        """

        _svc_name_ = SERVICE_NAME
        _svc_display_name_ = SERVICE_DISPLAY
        _svc_description_ = SERVICE_DESC

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self._stop_event = win32event.CreateEvent(None, 0, 0, None)
            self._process = None
            os.makedirs(LOG_DIR, exist_ok=True)

        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self._stop_event)
            if self._process and self._process.poll() is None:
                self._process.terminate()
                try:
                    self._process.wait(timeout=10)
                except Exception:
                    self._process.kill()

        def SvcDoRun(self):
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, ""),
            )
            self._run()

        def _run(self):
            """
            Loop principal: lanza bridge_server.py como subproceso.
            Si muere, espera 5s y lo relanza (máx. 10 reinicios por hora).
            """
            restart_times = []
            MAX_RESTARTS_PER_HOUR = 10

            log_out = open(
                os.path.join(LOG_DIR, "gravity_service.log"), "a", encoding="utf-8"
            )

            while True:
                # Verificar que no se ha solicitado stop
                if (
                    win32event.WaitForSingleObject(self._stop_event, 0)
                    == win32event.WAIT_OBJECT_0
                ):
                    break

                # Limpiar reinicios viejos (> 1 hora)
                now = time.time()
                restart_times = [t for t in restart_times if now - t < 3600]

                if len(restart_times) >= MAX_RESTARTS_PER_HOUR:
                    servicemanager.LogErrorMsg(
                        f"[GravityAI] Demasiados reinicios ({MAX_RESTARTS_PER_HOUR}/h). "
                        "Deteniendo servicio para evitar loop."
                    )
                    break

                # Lanzar bridge_server como subproceso hijo
                cmd = [PYTHON_EXE, BRIDGE_SCRIPT]
                self._process = subprocess.Popen(
                    cmd,
                    cwd=BASE_DIR,
                    stdout=log_out,
                    stderr=log_out,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )

                servicemanager.LogInfoMsg(
                    f"[GravityAI] Bridge Server iniciado (PID={self._process.pid})"
                )

                # Esperar a que el proceso termine o se solicite stop
                while True:
                    # Poll cada 2 segundos
                    ret = win32event.WaitForSingleObject(self._stop_event, 2000)
                    if ret == win32event.WAIT_OBJECT_0:
                        # Stop solicitado
                        if self._process.poll() is None:
                            self._process.terminate()
                        break
                    if self._process.poll() is not None:
                        # Proceso murió inesperadamente
                        exit_code = self._process.returncode
                        servicemanager.LogWarningMsg(
                            f"[GravityAI] Bridge Server terminó (exit={exit_code}). "
                            "Reiniciando en 5s..."
                        )
                        restart_times.append(time.time())
                        time.sleep(5)
                        break

                # Si se solicitó stop, salir del loop externo
                if (
                    win32event.WaitForSingleObject(self._stop_event, 0)
                    == win32event.WAIT_OBJECT_0
                ):
                    break

            log_out.close()

    HAS_PYWIN32 = True

except ImportError:
    HAS_PYWIN32 = False


# ── CLI de gestión del servicio ────────────────────────────────────────────────


def _run_sc(args: list, check=True) -> subprocess.CompletedProcess:
    return subprocess.run(["sc"] + args, capture_output=True, text=True, check=False)


def cmd_install():
    _require_admin()
    if not HAS_PYWIN32:
        print("[!] pywin32 no está instalado. Ejecuta: pip install pywin32")
        sys.exit(1)
    print(f"[+] Instalando servicio '{SERVICE_NAME}'...")
    win32serviceutil.HandleCommandLine(
        GravityWindowsService, argv=["gravity_service.py", "--startup=auto", "install"]
    )
    # Configurar recuperación automática ante fallos (3 intentos de reinicio)
    _run_sc(
        [
            "failure",
            SERVICE_NAME,
            "reset=",
            "3600",
            "actions=",
            "restart/5000/restart/10000/restart/30000",
        ]
    )
    print(f"[+] Servicio '{SERVICE_NAME}' instalado correctamente.")
    print("    Usa: python gravity_service.py start")


def cmd_start():
    _require_admin()
    print(f"[+] Iniciando servicio '{SERVICE_NAME}'...")
    r = _run_sc(["start", SERVICE_NAME])
    if r.returncode == 0 or "START_PENDING" in r.stdout or "RUNNING" in r.stdout:
        print("[+] Servicio iniciado correctamente.")
    else:
        print(f"[!] {r.stdout.strip() or r.stderr.strip()}")


def cmd_stop():
    _require_admin()
    print(f"[+] Deteniendo servicio '{SERVICE_NAME}'...")
    r = _run_sc(["stop", SERVICE_NAME])
    print(r.stdout.strip() or r.stderr.strip())


def cmd_restart():
    cmd_stop()
    time.sleep(3)
    cmd_start()


def cmd_remove():
    _require_admin()
    cmd_stop()
    time.sleep(2)
    print(f"[+] Desinstalando servicio '{SERVICE_NAME}'...")
    r = _run_sc(["delete", SERVICE_NAME])
    print(r.stdout.strip() or r.stderr.strip())


def cmd_status():
    r = _run_sc(["query", SERVICE_NAME])
    if r.returncode != 0:
        print(f"[!] Servicio '{SERVICE_NAME}' no instalado.")
    else:
        state = "DESCONOCIDO"
        for line in r.stdout.splitlines():
            if "STATE" in line:
                state = line.strip()
        print(f"[i] {state}")


def cmd_debug():
    """Corre bridge_server directamente (sin servicio) para pruebas."""
    print("[DEBUG] Iniciando bridge_server.py en primer plano...")
    os.execv(PYTHON_EXE, [PYTHON_EXE, BRIDGE_SCRIPT])


COMMANDS = {
    "install": cmd_install,
    "start": cmd_start,
    "stop": cmd_stop,
    "restart": cmd_restart,
    "remove": cmd_remove,
    "status": cmd_status,
    "debug": cmd_debug,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        # Detectar si pywin32 quiere manejar el proceso (cuando se lanza como servicio)
        if HAS_PYWIN32 and len(sys.argv) == 1:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(GravityWindowsService)
            servicemanager.StartServiceCtrlDispatcher()
        else:
            print(__doc__)
            print("Comandos disponibles:", ", ".join(COMMANDS.keys()))
    else:
        COMMANDS[sys.argv[1]]()
