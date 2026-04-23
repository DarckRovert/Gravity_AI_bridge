"""
Gravity AI — Session Runner V10.4 (Multi-Session Bridge)
Módulo derivado de OpenClaude para manejo de capacidad y spawn asíncrono.
"""

import threading
import time
import uuid
import subprocess
from typing import Optional, Dict

active_sessions: Dict[str, "SessionHandle"] = {}

class CapacityWake:
    """
    Señal de despertador (Wake Signal) para el poll-loop.
    Permite despertar al hilo bloqueado cuando se libera capacidad (una sesión termina).
    """
    def __init__(self):
        self._event = threading.Event()

    def wake(self):
        self._event.set()

    def wait(self, timeout: float) -> bool:
        """
        Espera hasta 'timeout' segundos.
        Retorna True si fue despertado por la señal, False si fue por timeout.
        """
        woke_up = self._event.wait(timeout)
        if woke_up:
            self._event.clear()
        return woke_up


class SessionHandle:
    """
    Handle que representa una sesión activa, encapsulando su proceso.
    """
    def __init__(self, session_id: str, process: subprocess.Popen):
        self.session_id = session_id
        self.process = process
        self.start_time = time.time()
        self.activities: list = []
        self.current_activity: Optional[Dict] = None

    def update_activity(self, activity: Dict):
        self.current_activity = activity
        self.activities.append(activity)
        # Mantener solo las últimas 5 actividades en historial
        if len(self.activities) > 5:
            self.activities.pop(0)

    def terminate(self):
        try:
            self.process.terminate()
        except Exception:
            pass


class SessionSpawner:
    """
    Manejador de creación de subprocesos de sesión asíncronas.
    """
    def __init__(self, python_executable: str = None, script_path: str = None):
        import sys, os
        self.python_exec = python_executable or sys.executable
        # Default a ask_deepseek.py en el root
        _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.script_path = script_path or os.path.join(_base, "ask_deepseek.py")

    def spawn(self, session_id: str, work_data: dict, role: str = None) -> SessionHandle:
        """
        Levanta un nuevo agente subproceso aislado.
        """
        cmd = [self.python_exec, self.script_path, "--session", session_id]
        if role:
            cmd.extend(["--role", role])
        
        # Iniciar proceso aislado
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8"
        )
        
        handle = SessionHandle(session_id, proc)
        active_sessions[session_id] = handle
        return handle

