"""
=============================================================================
        GRAVITY AI — SSH TUNNEL MANAGER V1.0 PRO [WoW Perú]
        Gestor de Túneles SSH con Auto-Reconexión y Watchdog
=============================================================================
Canaliza tráfico seguro desde el host local hacia el servidor remoto de
AzerothCore. Expone el puerto SOAP remoto (7878) en localhost de forma transparente.
"""

import os
import time
import socket
import logging
import threading
import subprocess
from typing import Dict, Any, Optional

log = logging.getLogger("gravity.tunnel")


class SSHTunnelManager:
    """
    Controla el proceso del túnel SSH en segundo plano usando el cliente
    OpenSSH nativo del sistema operativo.
    """

    def __init__(
        self,
        ssh_host: str,
        ssh_port: int = 22,
        ssh_user: str = "root",
        ssh_key: Optional[str] = None,
        local_port: int = 7878,
        remote_target_host: str = "127.0.0.1",
        remote_target_port: int = 7878,
        auto_reconnect: bool = True,
        reconnect_interval: int = 10,
    ) -> None:
        self.ssh_host = ssh_host
        self.ssh_port = int(ssh_port)
        self.ssh_user = ssh_user
        self.ssh_key = ssh_key
        self.local_port = int(local_port)
        self.remote_target_host = remote_target_host
        self.remote_target_port = int(remote_target_port)
        self.auto_reconnect = auto_reconnect
        self.reconnect_interval = reconnect_interval

        self._proc: Optional[subprocess.Popen] = None
        self._lock = threading.RLock()
        self._watchdog_thread: Optional[threading.Thread] = None
        self._should_run = False
        self._started_at: Optional[str] = None

    def _is_local_port_open(self, timeout: float = 0.5) -> bool:
        """Verifica si el puerto local ya responde a conexiones TCP."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex(("127.0.0.1", self.local_port)) == 0

    def _build_ssh_command(self) -> list:
        """Genera los argumentos de la línea de comandos de OpenSSH."""
        cmd = [
            "ssh",
            "-N",  # No ejecutar comando remoto (solo forwarding)
            "-L", f"{self.local_port}:{self.remote_target_host}:{self.remote_target_port}",
            "-p", str(self.ssh_port),
            "-o", "ExitOnForwardFailure=yes",
            "-o", "ServerAliveInterval=15",
            "-o", "ServerAliveCountMax=3",
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", "TCPKeepAlive=yes",
        ]

        if self.ssh_key and os.path.exists(self.ssh_key):
            cmd.extend(["-i", self.ssh_key])

        cmd.append(f"{self.ssh_user}@{self.ssh_host}")
        return cmd

    def start(self) -> Dict[str, Any]:
        """Inicia el túnel SSH y espera a que el puerto local esté disponible."""
        with self._lock:
            if self._proc and self._proc.poll() is None:
                if self._is_local_port_open():
                    return {"ok": True, "status": "already_running", "local_port": self.local_port}

            # Si el puerto local ya está ocupado por otro proceso o túnel previo
            if self._is_local_port_open():
                log.info(f"[Tunnel] El puerto {self.local_port} ya está activo. Asumiendo túnel previo.")
                self._should_run = True
                return {"ok": True, "status": "port_already_bound", "local_port": self.local_port}

            cmd = self._build_ssh_command()
            log.info(f"[Tunnel] Iniciando túnel SSH: {' '.join(cmd)}")

            creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

            try:
                self._proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=creation_flags,
                )
                self._should_run = True
                self._started_at = time.strftime("%Y-%m-%d %H:%M:%S")

                # Esperar hasta 5 segundos a que el puerto abra
                deadline = time.time() + 5.0
                while time.time() < deadline:
                    if self._proc.poll() is not None:
                        # Falló antes de abrir
                        _, stderr_data = self._proc.communicate()
                        err = stderr_data.decode("utf-8", errors="replace").strip()
                        log.error(f"[Tunnel] Fallo al iniciar túnel SSH: {err}")
                        return {"ok": False, "error": f"SSH terminated: {err}"}
                    if self._is_local_port_open():
                        log.info(f"[Tunnel] Túnel SSH establecido con éxito en localhost:{self.local_port}")
                        break
                    time.sleep(0.3)

                if not self._is_local_port_open():
                    try:
                        self._proc.terminate()
                    except Exception:
                        pass
                    return {
                        "ok": False,
                        "error": f"Timeout esperando puerto local {self.local_port}. Verifique autenticación SSH a {self.ssh_host}.",
                        "local_port": self.local_port,
                    }

                # Iniciar watchdog
                if self.auto_reconnect:
                    self._start_watchdog()

                return {
                    "ok": True,
                    "status": "connected",
                    "local_port": self.local_port,
                    "remote_target": f"{self.remote_target_host}:{self.remote_target_port}",
                    "pid": self._proc.pid,
                }

            except Exception as e:
                log.error(f"[Tunnel] Excepción iniciando túnel SSH: {e}")
                return {"ok": False, "error": str(e)}

    def stop(self) -> Dict[str, Any]:
        """Detiene el túnel SSH limpiamente."""
        with self._lock:
            self._should_run = False
            if self._proc:
                try:
                    self._proc.terminate()
                    self._proc.wait(timeout=3)
                except Exception:
                    try:
                        self._proc.kill()
                    except Exception:
                        pass
                self._proc = None

            log.info("[Tunnel] Túnel SSH detenido.")
            return {"ok": True, "status": "stopped"}

    def _start_watchdog(self) -> None:
        """Hilo de vigilancia para reconexión automática en caso de corte."""
        if self._watchdog_thread and self._watchdog_thread.is_alive():
            return

        def _watch():
            while self._should_run:
                time.sleep(self.reconnect_interval)
                with self._lock:
                    if not self._should_run:
                        break
                    proc_alive = self._proc and self._proc.poll() is None
                    port_alive = self._is_local_port_open()

                    if not proc_alive or not port_alive:
                        log.warning("[Tunnel Watchdog] Caída de túnel SSH detectada. Reconectando...")
                        self.start()

        self._watchdog_thread = threading.Thread(
            target=_watch,
            name=f"SSHTunnelWatchdog_{self.local_port}",
            daemon=True,
        )
        self._watchdog_thread.start()

    def is_active(self) -> bool:
        """Verifica si el puerto local está abierto y respondiendo."""
        return self._is_local_port_open()

    def get_status(self) -> Dict[str, Any]:
        """Consulta el estado del túnel."""
        with self._lock:
            is_proc_alive = self._proc is not None and self._proc.poll() is None
            is_port_open = self._is_local_port_open()
            return {
                "active": is_port_open,
                "process_alive": is_proc_alive,
                "local_port": self.local_port,
                "remote_target": f"{self.remote_target_host}:{self.remote_target_port}",
                "ssh_endpoint": f"{self.ssh_user}@{self.ssh_host}:{self.ssh_port}",
                "started_at": self._started_at,
            }


# ── Singleton facade ────────────────────────────────────────────────────────────
_tunnel: "SSHTunnelManager | None" = None
_tunnel_lock = threading.Lock()


def _load_wow_cfg() -> dict:
    try:
        from core.config_manager import config
        gs = config.get("game_servers", {})
        if not isinstance(gs, dict):
            gs = {}
        return gs.get("wow_peru", {})
    except Exception:
        return {}


def _get_tunnel() -> "SSHTunnelManager":
    global _tunnel
    with _tunnel_lock:
        if _tunnel is None:
            wow = _load_wow_cfg()
            _tunnel = SSHTunnelManager(
                ssh_host=wow.get("ssh_host", "login.wow-peru.lat"),
                ssh_port=int(wow.get("ssh_port", 22)),
                ssh_user=wow.get("ssh_user", ""),
                ssh_key=wow.get("ssh_key", ""),
                local_port=int(wow.get("soap_port", 7878)),
                remote_target_host="127.0.0.1",
                remote_target_port=int(wow.get("remote_soap_port", 7878)),
            )
    return _tunnel


def start_tunnel() -> dict:
    """Levanta el túnel SSH hacia WoW Perú."""
    t = _get_tunnel()
    t.start()
    return {"ok": True, "note": "Túnel SSH iniciado."}


def stop_tunnel() -> dict:
    """Cierra el túnel SSH."""
    t = _get_tunnel()
    t.stop()
    return {"ok": True, "note": "Túnel SSH detenido."}


def get_status() -> dict:
    """Estado del túnel SSH."""
    try:
        return _get_tunnel().get_status()
    except Exception as e:
        return {"active": False, "error": str(e)}

