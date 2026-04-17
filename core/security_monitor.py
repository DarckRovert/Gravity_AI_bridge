"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         GRAVITY AI — SECURITY MONITOR V9.4                                   ║
║         Monitor de procesos, puertos, integridad de archivos y red           ║
╚══════════════════════════════════════════════════════════════════════════════╝

Corre como daemon en background. Expone su estado via el bridge_server
en el endpoint GET /v1/security.

Capacidades:
  - Detección de procesos nuevos no vistos antes (usa psutil)
  - Escaneo de puertos abiertos vs lista blanca
  - Hash SHA-256 de archivos críticos del core para detectar modificaciones externas
  - Registro de alertas en _audit_log.jsonl
"""

import os
import json
import time
import hashlib
import threading
import subprocess
from datetime import datetime
from typing import Optional

import sys
# psutil es opcional — si no está instalado, el monitor opera en modo reducido
try:
    import psutil
    _PSUTIL_OK = True
except ImportError:
    _PSUTIL_OK = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Configuración ──────────────────────────────────────────────────────────────

# Puertos que el sistema usa legítimamente. Cualquier otro es sospechoso.
WHITELIST_PORTS: set[int] = {
    7860,   # Gravity Bridge
    7861,   # Fooocus
    11434,  # Ollama
    1234,   # LM Studio default
    8080,   # Jan AI
    8888,   # Jupyter (si aplica)
    443,    # HTTPS outbound
    80,     # HTTP outbound
    5432,   # Postgres (si aplica)
    3306,   # MySQL (si aplica)
    3724,   # WoW realmd
    8085,   # WoW worldserver
    7878,   # WoW SOAP api
}

# Archivos críticos cuyo hash se monitorea
CRITICAL_FILES: list[str] = [
    os.path.join(BASE_DIR, "bridge_server.py"),
    os.path.join(BASE_DIR, "ask_deepseek.py"),
    os.path.join(BASE_DIR, "_knowledge.json"),
    os.path.join(BASE_DIR, "core", "key_manager.py"),
    os.path.join(BASE_DIR, "core", "data_guardian.py"),
    os.path.join(BASE_DIR, "core", "provider_manager.py"),
]

SCAN_INTERVAL_SECONDS: int = 60

# ── Estado Global ──────────────────────────────────────────────────────────────

_state: dict = {
    "last_scan": None,
    "status": "initializing",
    "alerts": [],
    "processes": [],
    "open_ports": [],
    "suspicious_ports": [],
    "file_integrity": {},
    "psutil_available": _PSUTIL_OK,
}

_baseline_hashes: dict[str, str] = {}
_known_pids: set[int] = set()
_lock = threading.Lock()
_started = False


# ── Utilidades ─────────────────────────────────────────────────────────────────

def _sha256(path: str) -> Optional[str]:
    """Calcula el hash SHA-256 de un archivo."""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def _record_alert(level: str, message: str) -> None:
    """Registra una alerta en el estado y en el audit log."""
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": level,
        "message": message,
        "source": "security_monitor",
    }
    with _lock:
        _state["alerts"].append(entry)
        # Mantener solo las últimas 100 alertas en memoria
        if len(_state["alerts"]) > 100:
            _state["alerts"] = _state["alerts"][-100:]

    # Log al archivo de auditoría
    try:
        audit_path = os.path.join(BASE_DIR, "_audit_log.jsonl")
        with open(audit_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ── Escaneos ───────────────────────────────────────────────────────────────────

def _scan_processes() -> list[dict]:
    """Detecta procesos nuevos vs los conocidos al arranque."""
    if not _PSUTIL_OK:
        return [{"note": "psutil no disponible — instalar con: pip install psutil"}]

    current_pids = set()
    procs = []
    try:
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info", "status"]):
            try:
                info = proc.info
                pid = info["pid"]
                current_pids.add(pid)
                if pid not in _known_pids:
                    _record_alert(
                        "INFO",
                        f"Nuevo proceso detectado: {info['name']} (PID {pid})"
                    )
                procs.append({
                    "pid":    pid,
                    "name":   info.get("name", "?"),
                    "cpu":    round(info.get("cpu_percent", 0.0), 1),
                    "mem_mb": round((info.get("memory_info") or type("o", (), {"rss": 0})()).rss / 1024 / 1024, 1),
                    "status": info.get("status", "?"),
                    "new":    pid not in _known_pids,
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass

    _known_pids.update(current_pids)
    # Ordenar por CPU descendente, mostrar los 30 más activos
    procs.sort(key=lambda x: x["cpu"], reverse=True)
    return procs[:30]


def _scan_ports() -> tuple[list[dict], list[int]]:
    """Escanea puertos TCP escuchando en la máquina local."""
    if not _PSUTIL_OK:
        return [], []

    open_ports = []
    suspicious = []

    try:
        for conn in psutil.net_connections(kind="tcp"):
            if conn.status == "LISTEN":
                port = conn.laddr.port
                try:
                    proc_name = psutil.Process(conn.pid).name() if conn.pid else "?"
                except Exception:
                    proc_name = "?"
                is_suspicious = port not in WHITELIST_PORTS and port > 1024
                if is_suspicious:
                    suspicious.append(port)
                    _record_alert(
                        "WARNING",
                        f"Puerto no reconocido en escucha: {port} (proceso: {proc_name})"
                    )
                open_ports.append({
                    "port":      port,
                    "process":   proc_name,
                    "pid":       conn.pid,
                    "suspicious": is_suspicious,
                })
    except Exception:
        pass

    open_ports.sort(key=lambda x: x["port"])
    return open_ports, suspicious


def _scan_file_integrity() -> dict[str, dict]:
    """Verifica integridad SHA-256 de archivos críticos contra el baseline."""
    results = {}
    for path in CRITICAL_FILES:
        fname = os.path.basename(path)
        current_hash = _sha256(path)
        baseline_hash = _baseline_hashes.get(path)

        if current_hash is None:
            results[fname] = {"status": "not_found", "hash": None}
            continue

        if baseline_hash is None:
            # Primera vez: establecer baseline
            _baseline_hashes[path] = current_hash
            results[fname] = {"status": "baseline_set", "hash": current_hash[:12] + "..."}
        elif current_hash != baseline_hash:
            _record_alert(
                "CRITICAL",
                f"Modificación externa detectada en archivo crítico: {fname}"
            )
            results[fname] = {
                "status": "MODIFIED",
                "hash": current_hash[:12] + "...",
                "baseline": baseline_hash[:12] + "...",
            }
        else:
            results[fname] = {"status": "ok", "hash": current_hash[:12] + "..."}

    return results


# ── Loop Principal ─────────────────────────────────────────────────────────────

def _monitor_loop() -> None:
    """Loop daemon que ejecuta todos los escaneos periódicamente."""
    while True:
        try:
            procs = _scan_processes()
            ports, suspicious = _scan_ports()
            integrity = _scan_file_integrity()

            with _lock:
                _state["last_scan"] = datetime.utcnow().isoformat() + "Z"
                _state["status"] = "ok" if not suspicious else "warning"
                _state["processes"] = procs
                _state["open_ports"] = ports
                _state["suspicious_ports"] = suspicious
                _state["file_integrity"] = integrity

        except Exception as e:
            with _lock:
                _state["status"] = "error"
                _state["last_scan"] = datetime.utcnow().isoformat() + "Z"

        time.sleep(SCAN_INTERVAL_SECONDS)


# ── API Pública ────────────────────────────────────────────────────────────────

def get_state() -> dict:
    """Retorna el estado actual del monitor (thread-safe)."""
    with _lock:
        return dict(_state)


def force_scan() -> dict:
    """Fuerza un escaneo inmediato y retorna el resultado."""
    procs = _scan_processes()
    ports, suspicious = _scan_ports()
    integrity = _scan_file_integrity()

    with _lock:
        _state["last_scan"] = datetime.utcnow().isoformat() + "Z"
        _state["status"] = "ok" if not suspicious else "warning"
        _state["processes"] = procs
        _state["open_ports"] = ports
        _state["suspicious_ports"] = suspicious
        _state["file_integrity"] = integrity
        return dict(_state)


def start() -> None:
    """Inicia el monitor de seguridad como daemon thread."""
    global _started
    if _started:
        return
    _started = True

    # Baseline inicial de hashes
    for path in CRITICAL_FILES:
        h = _sha256(path)
        if h:
            _baseline_hashes[path] = h

    # Capturar PIDs actuales como "conocidos" al arranque
    if _PSUTIL_OK:
        try:
            for proc in psutil.process_iter(["pid"]):
                try:
                    _known_pids.add(proc.info["pid"])
                except Exception:
                    pass
        except Exception:
            pass

    t = threading.Thread(
        target=_monitor_loop,
        name="GravitySecurityMonitor",
        daemon=True,
    )
    t.start()
