"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — MCP ADAPTER V13.0 PRO                                              ║
║  Model Context Protocol — Stdio Bridge con robustez de producción            ║
╚══════════════════════════════════════════════════════════════════════════════╝

Cambios V13.0 PRO (vs V13.0 PRO):
  - Timeout de 10s en readline() via queue.Queue + thread reader (threading puro,
    compatible con ThreadingHTTPServer — NO usa asyncio.wait_for)
  - Reconexión con backoff exponencial: 1s → 2s → 4s → 8s … max 30s
  - Health check periódico cada 60s en daemon thread
  - _id_counter protegido con lock para thread-safety
  - import de time añadido (faltaba en V13.0 PRO)
"""

import json
import subprocess
import threading
import time
import queue
import logging
from typing import Dict, Any, List, Optional

log = logging.getLogger("gravity.mcp_adapter")

# Registro global de adaptadores activos
active_adapters: Dict[str, "MCPAdapter"] = {}

# Backoff config
_BACKOFF_INITIAL = 1.0   # segundos
_BACKOFF_MAX     = 30.0  # segundos
_READ_TIMEOUT    = 10.0  # segundos para readline()
_HEALTH_INTERVAL = 60    # segundos entre health checks


class MCPAdapter:
    """
    Adaptador para servidores MCP que operan vía stdio (JSON-RPC 2.0).

    Thread-safety:
      - _id_counter protegido con _counter_lock
      - _read_line_timeout() usa un thread lector + queue para timeout sin asyncio
      - health check corre en daemon thread

    Reconexión:
      - Backoff exponencial: 1, 2, 4, 8, 16, 30s (máximo)
    """

    def __init__(
        self,
        server_path: str,
        args: Optional[List[str]] = None,
        name: str = "default",
    ) -> None:
        self.server_path  = server_path
        self.args         = args if args is not None else []
        self.name         = name
        self.process: Optional[subprocess.Popen] = None

        self._id_counter  = 1
        self._counter_lock = threading.Lock()
        self._conn_lock    = threading.Lock()
        self._backoff      = _BACKOFF_INITIAL
        self._health_thread: Optional[threading.Thread] = None

        # Registrar globalmente
        active_adapters[self.name] = self
        self._start_health_daemon()

    # ── Conexión ──────────────────────────────────────────────────────────────

    def connect(self) -> bool:
        """Inicia el proceso del servidor MCP. Thread-safe."""
        with self._conn_lock:
            if self.process and self.process.poll() is None:
                return True
            return self._do_connect()

    def _do_connect(self) -> bool:
        """Intenta conectar sin adquirir _conn_lock (ya debe estar adquirido)."""
        try:
            cmd = [self.server_path] + self.args
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                bufsize=1,
            )
            time.sleep(0.3)
            if self.process.poll() is not None:
                log.warning(f"[MCP:{self.name}] Proceso terminó inmediatamente tras connect.")
                self.process = None
                return False
            log.info(f"[MCP:{self.name}] Conectado (PID {self.process.pid})")
            self._backoff = _BACKOFF_INITIAL  # reset backoff en éxito
            return True
        except Exception as e:
            log.error(f"[MCP:{self.name}] Error al conectar: {e}")
            self.process = None
            return False

    def _reconnect_with_backoff(self) -> bool:
        """
        Reconexión con backoff exponencial.
        Intenta hasta que tiene éxito o alcanza _BACKOFF_MAX en el último intento.
        """
        delay = self._backoff
        while True:
            log.info(f"[MCP:{self.name}] Reconectando en {delay:.1f}s...")
            time.sleep(delay)
            with self._conn_lock:
                if self._do_connect():
                    return True
            delay = min(delay * 2, _BACKOFF_MAX)
            if delay >= _BACKOFF_MAX:
                # Un intento más al máximo y salimos
                time.sleep(delay)
                with self._conn_lock:
                    return self._do_connect()

    # ── I/O con timeout ───────────────────────────────────────────────────────

    def _next_id(self) -> int:
        """Genera un ID único de request de forma thread-safe."""
        with self._counter_lock:
            rid = self._id_counter
            self._id_counter += 1
        return rid

    def _read_line_timeout(self, timeout: float = _READ_TIMEOUT) -> Optional[str]:
        """
        Lee una línea de stdout con timeout real.

        Implementación: thread lector + queue.Queue en lugar de asyncio.wait_for,
        compatible con ThreadingHTTPServer (sin event loop de asyncio).

        Returns:
            Línea leída, o None si hubo timeout o el proceso terminó.
        """
        if not self.process or not self.process.stdout:
            return None

        result_q: queue.Queue[Optional[str]] = queue.Queue(maxsize=1)

        def _reader() -> None:
            try:
                line = self.process.stdout.readline()  # type: ignore[union-attr]
                result_q.put(line if line else None)
            except Exception:
                result_q.put(None)

        t = threading.Thread(target=_reader, daemon=True, name=f"MCPReader-{self.name}")
        t.start()

        try:
            line = result_q.get(timeout=timeout)
            return line
        except queue.Empty:
            log.warning(f"[MCP:{self.name}] Timeout de {timeout}s esperando respuesta.")
            return None

    def _send_request(self, method: str, params: dict) -> Dict[str, Any]:
        """
        Envía una request JSON-RPC y espera la respuesta.
        Reconecta con backoff si el proceso no está disponible.
        """
        if not self.connect():
            if not self._reconnect_with_backoff():
                return {"error": f"[MCP:{self.name}] No se pudo reconectar."}

        request = {
            "jsonrpc": "2.0",
            "id":      self._next_id(),
            "method":  method,
            "params":  params,
        }

        try:
            payload = json.dumps(request) + "\n"
            self.process.stdin.write(payload)   # type: ignore[union-attr]
            self.process.stdin.flush()           # type: ignore[union-attr]
        except Exception as e:
            log.error(f"[MCP:{self.name}] Error al escribir en stdin: {e}")
            # Proceso muerto — reconectar
            self._reconnect_with_backoff()
            return {"error": f"Fallo al enviar request: {e}"}

        line = self._read_line_timeout(_READ_TIMEOUT)
        if line is None:
            return {"error": f"[MCP:{self.name}] Sin respuesta (timeout {_READ_TIMEOUT}s)"}

        try:
            return json.loads(line)
        except json.JSONDecodeError as e:
            return {"error": f"[MCP:{self.name}] JSON inválido: {e} | raw: {line[:200]}"}

    # ── API Pública ───────────────────────────────────────────────────────────

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza una llamada a una herramienta del servidor MCP."""
        return self._send_request("tools/call", {"name": tool_name, "arguments": arguments})

    def list_tools(self) -> List[Dict[str, Any]]:
        """Solicita la lista de herramientas disponibles."""
        resp = self._send_request("tools/list", {})
        return resp.get("result", {}).get("tools", []) if "error" not in resp else []

    def list_resources(self) -> List[Dict[str, Any]]:
        """Solicita la lista de recursos del servidor MCP."""
        resp = self._send_request("resources/list", {})
        return resp.get("result", {}).get("resources", []) if "error" not in resp else []

    def read_resource(self, uri: str) -> Dict[str, Any]:
        """Lee un recurso específico."""
        return self._send_request("resources/read", {"uri": uri})

    def disconnect(self) -> None:
        """Detiene el servidor MCP y libera recursos."""
        with self._conn_lock:
            if self.process:
                try:
                    self.process.terminate()
                    self.process.wait(timeout=5)
                except Exception:
                    try:
                        self.process.kill()
                    except Exception:
                        pass
                self.process = None
        log.info(f"[MCP:{self.name}] Desconectado.")

    def health_check(self) -> bool:
        """Verifica si el proceso está activo sin enviar una request."""
        with self._conn_lock:
            return self.process is not None and self.process.poll() is None

    # ── Health Daemon ─────────────────────────────────────────────────────────

    def _start_health_daemon(self) -> None:
        """Inicia un daemon que verifica el proceso cada _HEALTH_INTERVAL segundos."""
        if self._health_thread and self._health_thread.is_alive():
            return

        def _health_loop() -> None:
            while True:
                time.sleep(_HEALTH_INTERVAL)
                try:
                    alive = self.health_check()
                    if not alive:
                        log.warning(
                            f"[MCP:{self.name}] Health check falló — proceso muerto. "
                            f"Iniciando reconexión con backoff..."
                        )
                        self._reconnect_with_backoff()
                    else:
                        log.debug(f"[MCP:{self.name}] Health check OK.")
                except Exception as e:
                    log.warning(f"[MCP:{self.name}] Error en health daemon: {e}")

        self._health_thread = threading.Thread(
            target=_health_loop,
            name=f"MCPHealth_{self.name}",
            daemon=True,
        )
        self._health_thread.start()
