"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         GRAVITY AI — SECURITY MONITOR V16.0 PRO [Diamond-Tier Edition]       ║
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
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Set, Tuple

# psutil es opcional — si no está instalado, el monitor opera en modo reducido
try:
    import psutil
    _PSUTIL_OK = True
except ImportError:
    _PSUTIL_OK = False

BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Configuración ──────────────────────────────────────────────────────────────

# Puertos conocidos del ecosistema Gravity. Cualquier otro se evalúa por proceso.
WHITELIST_PORTS: Set[int] = {
    7860,   # Gravity Bridge
    7861,   # Fooocus
    7862,   # Fooocus Studio UI
    7863,   # V2V WebSocket Engine
    11434,  # Ollama
    1234,   # LM Studio default
    8080,   # Jan AI / HTTP alt
    8888,   # Jupyter
    443,    # HTTPS
    80,     # HTTP
    5432,   # Postgres
    3306,   # MySQL
    3724,   # WoW realmd
    8085,   # WoW worldserver
    7878,   # WoW SOAP api
    8181,   # Jan AI alt
    1080,   # proxy local
    5000,   # Flask / devtools
    3000,   # Node DevServer
    4000,   # GraphQL / dev
    9090,   # Prometheus
    9229,   # Node debugger
    8188,   # ComfyUI
}

# Procesos legítimos que pueden abrir puertos aleatorios sin ser sospechosos.
# Los comparamos en lowercase para ser case-insensitive.
LEGITIMATE_PROCESS_NAMES: Set[str] = {
    # Sistema operativo Windows
    "svchost.exe", "lsass.exe", "wininit.exe", "services.exe",
    "explorer.exe", "winlogon.exe", "spoolsv.exe", "taskmgr.exe",
    "audiodg.exe", "dwm.exe", "csrss.exe", "smss.exe",
    # Navegadores
    "chrome.exe", "firefox.exe", "msedge.exe", "brave.exe", "opera.exe",
    "iexplore.exe", "chromium.exe", "vivaldi.exe",
    # Comunicación
    "discord.exe", "slack.exe", "teams.exe", "zoom.exe", "skype.exe",
    "telegram.exe", "whatsapp.exe", "signal.exe",
    # Gaming / distribución
    "steam.exe", "epicgameslauncher.exe", "gog galaxy.exe", "upc.exe",
    "battlenet.exe", "origin.exe", "eadesktop.exe",
    # Desarrollo
    "node.exe", "python.exe", "python3.exe", "code.exe", "git.exe",
    "java.exe", "javaw.exe", "cargo.exe", "rustup.exe",
    # Herramientas comunes
    "dropbox.exe", "onedrive.exe", "googledrivefs.exe", "syncthing.exe",
    "nordvpn.exe", "mullvad.exe", "protonvpn.exe", "tailscale.exe",
    "docker.exe", "dockerd.exe", "wsl.exe", "wslhost.exe",
    # Gravity / IA local
    "gravitybridge.exe", "lm studio.exe", "lmstudio.exe",
    "ollama.exe", "jan.exe", "koboldcpp.exe",
}

# Herramientas de hacking / debugging prohibidas (Anti-Tampering)
BLACKLIST_TOOLS: Set[str] = {
    "x64dbg.exe", "x32dbg.exe", "cheatengine-x86_64.exe", "cheatengine-i386.exe",
    "procdump.exe", "procdump64.exe", "processhacker.exe", "wireshark.exe",
    "tcpview.exe", "fiddler.exe", "burpsuite.exe", "ollydbg.exe", "ida64.exe"
}

MAX_IO_WRITE_MB = 500  # Limite de escritura sospechosa (MB)

# Archivos críticos cuyo hash se monitorea
CRITICAL_FILES: List[str] = [
    os.path.join(BASE_DIR, "bridge_server.py"),
    os.path.join(BASE_DIR, "ask_deepseek.py"),
    os.path.join(BASE_DIR, "_knowledge.json"),
    os.path.join(BASE_DIR, "core", "key_manager.py"),
    os.path.join(BASE_DIR, "core", "data_guardian.py"),
    os.path.join(BASE_DIR, "core", "provider_manager.py"),
]

SCAN_INTERVAL_SECONDS: int = 60
ACTIVE_DEFENSE: bool = True  # Transformar de IDS (monitoreo pasivo) a IPS (defensa letal activa)

# ── Estado Global ──────────────────────────────────────────────────────────────

_state: Dict[str, Any] = {
    "last_scan": None,
    "status": "initializing",
    "score": 100,
    "alerts": [],
    "processes": [],
    "open_ports": [],
    "suspicious_ports": [],
    "file_integrity": {},
    "banned_ips": [],
    "killed_tools": [],
    "psutil_available": _PSUTIL_OK,
    "scans_today": 0,
}

_baseline_hashes: Dict[str, str] = {}
_known_pids: Set[int] = set()
_lock: threading.RLock = threading.RLock()
_started: bool = False


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
    """Registra una alerta en el estado y en el audit log bajo RLock."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "level": level,
        "message": message,
        "source": "security_monitor",
    }
    with _lock:
        _state["alerts"].append(entry)
        # Mantener solo las últimas 100 alertas en memoria
        if len(_state["alerts"]) > 100:
            _state["alerts"] = _state["alerts"][-100:]

        # Log al archivo de auditoría de forma completamente thread-safe
        try:
            audit_path = os.path.join(BASE_DIR, "_audit_log.jsonl")
            with open(audit_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass


# ── Escaneos ───────────────────────────────────────────────────────────────────

def _scan_processes() -> List[Dict[str, Any]]:
    """Detecta procesos nuevos vs los conocidos al arranque."""
    if not _PSUTIL_OK:
        return [{"note": "psutil no disponible — instalar con: pip install psutil"}]

    current_pids: Set[int] = set()
    procs: List[Dict[str, Any]] = []
    try:
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info", "status"]):
            try:
                info = proc.info
                pid = info["pid"]
                current_pids.add(pid)
                
                with _lock:
                    is_new = pid not in _known_pids
                
                if is_new:
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
                    "new":    is_new,
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass

    with _lock:
        _known_pids.update(current_pids)
    
    # Ordenar por CPU descendente, mostrar los 30 más activos
    procs.sort(key=lambda x: x["cpu"], reverse=True)
    return procs[:30]


def _scan_ports() -> Tuple[List[Dict[str, Any]], List[int]]:
    """Escanea puertos TCP escuchando. Solo marca sospechoso si el proceso
    dueño del puerto NO está en la lista de procesos legítimos conocidos.
    Esto elimina los falsos positivos de puertos efímeros de Steam, Discord, etc.
    """
    if not _PSUTIL_OK:
        return [], []

    open_ports: List[Dict[str, Any]] = []
    suspicious: List[int] = []

    try:
        for conn in psutil.net_connections(kind="tcp"):
            if conn.status != "LISTEN":
                continue
            port = conn.laddr.port
            proc_name = "?"
            proc_name_lower = ""
            try:
                if conn.pid:
                    p_name = psutil.Process(conn.pid).name()
                    proc_name = p_name if p_name else "?"
                    proc_name_lower = proc_name.lower()
            except Exception:
                pass

            # Un puerto es sospechoso si no está en la whitelist estricta.
            # Endurecimiento: python/node NO tienen pase libre para abrir cualquier puerto.
            in_port_whitelist    = port in WHITELIST_PORTS
            is_legitimate_proc   = proc_name_lower in LEGITIMATE_PROCESS_NAMES
            is_system_proc       = proc_name_lower in ["svchost.exe", "system", "lsass.exe", "wininit.exe", "services.exe", "spoolsv.exe", "smss.exe"]

            if is_legitimate_proc:
                # Si es un intérprete, SOLO puede abrir puertos conocidos del ecosistema
                is_suspicious = not in_port_whitelist
            else:
                # Los puertos del sistema (<1024) solo son seguros si el proceso dueño es crítico de Windows
                is_system_port = port <= 1024
                if is_system_port and is_system_proc:
                    is_suspicious = False
                else:
                    is_suspicious = not in_port_whitelist

            if is_suspicious:
                suspicious.append(port)
                alert_msg = f"Puerto no reconocido en escucha: {port} (proceso: {proc_name})"
                
                # IPS: Defensa Activa (Matar proceso)
                killed = False
                if ACTIVE_DEFENSE and conn.pid:
                    try:
                        psutil.Process(conn.pid).kill()
                        alert_msg += f" -> [DEFENSA ACTIVA] Proceso PID {conn.pid} aniquilado."
                        _record_alert("ACTION", alert_msg)
                        killed = True
                    except Exception as e:
                        alert_msg += f" -> [FALLO DEFENSA] Error al matar: {e}"
                
                if not killed:
                    _record_alert("WARNING", alert_msg)

            open_ports.append({
                "port":       port,
                "process":    proc_name,
                "pid":        conn.pid,
                "suspicious": is_suspicious,
            })
    except Exception:
        pass

    open_ports.sort(key=lambda x: x["port"])
    return open_ports, suspicious


def _scan_file_integrity() -> Dict[str, Dict[str, Any]]:
    """Verifica integridad SHA-256 de archivos críticos contra el baseline."""
    results: Dict[str, Dict[str, Any]] = {}
    for path in CRITICAL_FILES:
        fname = os.path.basename(path)
        current_hash = _sha256(path)
        
        with _lock:
            baseline_hash = _baseline_hashes.get(path)

        if current_hash is None:
            results[fname] = {"status": "not_found", "hash": None}
            continue

        if baseline_hash is None:
            # Primera vez: establecer baseline
            with _lock:
                _baseline_hashes[path] = current_hash
            results[fname] = {"status": "baseline_set", "hash": current_hash[:12] + "..."}
        elif current_hash != baseline_hash:
            alert_msg = f"Modificación externa detectada en archivo crítico: {fname}"
            
            # IPS: Defensa Activa (Curación por Git Restore)
            restored = False
            if ACTIVE_DEFENSE:
                try:
                    # Sobreescribimos cualquier inyección restaurando del repositorio git
                    subprocess.run(["git", "restore", path], cwd=BASE_DIR, check=True)
                    new_hash = _sha256(path)
                    with _lock:
                        if new_hash:
                            _baseline_hashes[path] = new_hash
                            
                    alert_msg += " -> [DEFENSA ACTIVA] Archivo curado y restaurado vía Git."
                    _record_alert("ACTION", alert_msg)
                    results[fname] = {"status": "RESTORED", "hash": new_hash[:12] + "..." if new_hash else "?"}
                    restored = True
                except Exception as e:
                    alert_msg += f" -> [FALLO DEFENSA] No se pudo restaurar: {e}"
            
            if not restored:
                _record_alert("CRITICAL", alert_msg)
                results[fname] = {
                    "status": "MODIFIED",
                    "hash": current_hash[:12] + "...",
                    "baseline": baseline_hash[:12] + "...",
                }
        else:
            results[fname] = {"status": "ok", "hash": current_hash[:12] + "..."}

    return results


def _scan_anti_tampering() -> List[str]:
    """
    Detecta y aniquila herramientas de debugging o análisis de memoria (Anti-Dump).
    [!] LIMITACIÓN ZERO-TRUST: La detección se basa en nombres de proceso exactos.
    Un atacante puede evadir esto renombrando el ejecutable malicioso.
    Solución futura: Integración con reglas YARA o firmas SHA-256 en memoria.
    """
    if not _PSUTIL_OK:
        return []
        
    killed = []
    try:
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = (proc.info.get("name") or "").lower()
                if name in BLACKLIST_TOOLS:
                    if ACTIVE_DEFENSE:
                        proc.kill()
                        _record_alert("CRITICAL", f"[ANTI-TAMPERING] Herramienta prohibida aniquilada: {name} (PID {proc.info['pid']})")
                    else:
                        _record_alert("WARNING", f"[ANTI-TAMPERING] Herramienta prohibida detectada: {name}")
                    killed.append(name)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass
    return killed


def _scan_process_behavior() -> None:
    """Previene ejecución de comandos shell desde procesos sensibles (Prevención RCE)."""
    if not _PSUTIL_OK:
        return
        
    try:
        my_pid = os.getpid()
        for proc in psutil.process_iter(["pid", "name", "ppid"]):
            try:
                name = (proc.info.get("name") or "").lower()
                ppid = proc.info.get("ppid")
                
                # Shells ejecutados directamente por Gravity
                if name in ["cmd.exe", "powershell.exe", "pwsh.exe", "bash.exe", "sh.exe"]:
                    if ppid == my_pid:
                        # Evitar falsos positivos: revisar cmdline
                        try:
                            cmd_list = proc.cmdline()
                            if cmd_list and len(cmd_list) > 1:
                                import re
                                # El primer argumento es la shell. Extraemos el comando real.
                                full_cmd = " ".join(cmd_list[1:]).lower()
                                # Limpiar flags comunes de ejecución y comillas
                                full_cmd = re.sub(r'^(?:/c|-c|-command)\s+', '', full_cmd).strip(' "\'')
                                
                                # Whitelist estricta: el comando DEBE empezar con el binario legítimo
                                safe_cmds = ["git ", "pip ", "npm ", "uv ", "build", "conda ", "activate "]
                                if any(full_cmd.startswith(safe) for safe in safe_cmds):
                                    continue
                        except Exception:
                            pass
                        
                        if ACTIVE_DEFENSE:
                            try:
                                proc.kill()
                                _record_alert("CRITICAL", f"[ANTI-RCE] Intento de shell sospechoso bloqueado: {name} (PID {proc.info['pid']})")
                            except psutil.NoSuchProcess:
                                pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass


def _scan_network_threats() -> List[str]:
    """Banea IPs externas que realicen un número excesivo de conexiones concurrentes (Anti-DoS/Brute-Force)."""
    if not _PSUTIL_OK:
        return []
    
    banned = []
    ip_connections = {}
    MAX_CONCURRENT_CONNECTIONS = 50  # Umbral para considerar DoS/DDoS
    
    try:
        for conn in psutil.net_connections(kind="tcp"):
            if conn.raddr:
                r_ip = conn.raddr.ip
                l_port = conn.laddr.port
                
                # Ignorar IPs locales (Loopback y LAN)
                if r_ip and not (r_ip.startswith("127.") or r_ip.startswith("192.168.") or r_ip.startswith("10.") or r_ip == "::1"):
                    # Solo contar conexiones concurrentes a los puertos de Gravity
                    if l_port in WHITELIST_PORTS:
                        ip_connections[r_ip] = ip_connections.get(r_ip, 0) + 1

        for r_ip, count in ip_connections.items():
            if count > MAX_CONCURRENT_CONNECTIONS and ACTIVE_DEFENSE:
                with _lock:
                    if r_ip not in _state.get("banned_ips", []):
                        cmd = f'netsh advfirewall firewall add rule name="GravityBan_DoS_{r_ip}" dir=in action=block remoteip={r_ip}'
                        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        _state.setdefault("banned_ips", []).append(r_ip)
                        banned.append(r_ip)
                        _record_alert("CRITICAL", f"[FIREWALL] IP externa {r_ip} bloqueada por ataque DoS ({count} conexiones simultáneas)")
    except Exception:
        pass
    return banned


def _scan_io_anomalies() -> None:
    """Busca procesos con alta I/O que podrían ser ransomware."""
    if not _PSUTIL_OK:
        return
        
    try:
        for proc in psutil.process_iter(["pid", "name", "io_counters"]):
            try:
                io = proc.info.get("io_counters")
                if io:
                    write_mb = io.write_bytes / (1024 * 1024)
                    if write_mb > MAX_IO_WRITE_MB:
                        name = (proc.info.get("name") or "").lower()
                        
                        # Prevenir falsos positivos: Whitelist de ejecutables y directorios confiables
                        exe_path = ""
                        try:
                            exe_path = proc.exe().lower() if proc.exe() else ""
                        except Exception:
                            # Si no tenemos permisos para ver el exe, suele ser un proceso clave del sistema (NT AUTHORITY)
                            # Lo ignoramos para no congelar el sistema operativo entero.
                            continue
                            
                        # Prevenir falsos positivos: Whitelist de directorios confiables absolutos
                        safe_prefixes = [
                            "c:\\windows\\", 
                            "c:\\program files\\", 
                            "c:\\program files (x86)\\"
                        ]
                        # Evitar bypasses (ej. carpeta "steam" en el escritorio de un usuario)
                        is_safe_dir = any(exe_path.startswith(p) for p in safe_prefixes)
                        is_game_dir = ("\\steam\\" in exe_path or "\\epic games\\" in exe_path) and not exe_path.startswith("c:\\users\\")
                        
                        if is_safe_dir or is_game_dir:
                            continue

                        if name not in LEGITIMATE_PROCESS_NAMES and name not in BLACKLIST_TOOLS:
                            if ACTIVE_DEFENSE:
                                proc.suspend()
                                _record_alert("CRITICAL", f"[ANTI-RANSOMWARE] I/O masivo detectado ({write_mb:.1f} MB). Proceso SUSPENDIDO: {name}")
                            else:
                                _record_alert("WARNING", f"[ANTI-RANSOMWARE] I/O masivo en {name}: {write_mb:.1f} MB.")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass


# ── Loop Principal ─────────────────────────────────────────────────────────────

def _monitor_loop() -> None:
    """Loop daemon que ejecuta todos los escaneos periódicamente."""
    while True:
        try:
            procs = _scan_processes()
            ports, suspicious = _scan_ports()
            integrity = _scan_file_integrity()
            
            # Nuevos escaneos EDR
            killed_tools = _scan_anti_tampering()
            _scan_process_behavior()
            banned_ips = _scan_network_threats()
            _scan_io_anomalies()

            # Calcular score real: 100 - penalizaciones por alertas
            with _lock:
                recent_alerts = _state["alerts"][-20:]
            critical_count = sum(1 for a in recent_alerts if a.get("level") == "CRITICAL")
            warning_count  = sum(1 for a in recent_alerts if a.get("level") == "WARNING")
            computed_score = max(0, 100 - critical_count * 20 - warning_count * 5 - len(suspicious) * 10)

            # Rotación automática del audit log si supera 10 MB (BUG-08) bajo RLock
            try:
                audit_path = os.path.join(BASE_DIR, "_audit_log.jsonl")
                with _lock:
                    if os.path.isfile(audit_path) and os.path.getsize(audit_path) > 10 * 1024 * 1024:
                        import shutil as _sh
                        archive_dir = os.path.join(BASE_DIR, "_archivo")
                        os.makedirs(archive_dir, exist_ok=True)
                        ts_rot = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                        _sh.move(audit_path, os.path.join(archive_dir, f"audit_{ts_rot}.jsonl"))
            except Exception:
                pass  # No bloquear el monitor si la rotación falla

            with _lock:
                _state["last_scan"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                _state["status"] = "ok" if not suspicious else "warning"
                _state["score"] = computed_score
                _state["processes"] = procs
                _state["open_ports"] = ports
                _state["suspicious_ports"] = suspicious
                _state["file_integrity"] = integrity
                
                # Extender estado
                if killed_tools:
                    _state.setdefault("killed_tools", []).extend(killed_tools)
                
                _state["scans_today"] = _state.get("scans_today", 0) + 1

        except Exception:
            with _lock:
                _state["status"] = "error"
                _state["last_scan"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        time.sleep(SCAN_INTERVAL_SECONDS)


# ── API Pública ────────────────────────────────────────────────────────────────

def get_state() -> Dict[str, Any]:
    """Retorna el estado actual del monitor (thread-safe)."""
    with _lock:
        return dict(_state)


def scan_processes() -> List[Dict[str, Any]]:
    """Alias público de _scan_processes(). Usado por mixin_post /v1/security/scan."""
    return _scan_processes()


def force_scan() -> Dict[str, Any]:
    """Fuerza un escaneo inmediato y retorna el resultado."""
    procs = _scan_processes()
    ports, suspicious = _scan_ports()
    integrity = _scan_file_integrity()
    
    killed_tools = _scan_anti_tampering()
    _scan_process_behavior()
    banned_ips = _scan_network_threats()
    _scan_io_anomalies()

    with _lock:
        _state["last_scan"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        _state["status"] = "ok" if not suspicious else "warning"
        _state["processes"] = procs
        _state["open_ports"] = ports
        _state["suspicious_ports"] = suspicious
        _state["file_integrity"] = integrity
        
        if killed_tools:
            _state.setdefault("killed_tools", []).extend(killed_tools)
            
        _state["scans_today"] = _state.get("scans_today", 0) + 1
        return dict(_state)


def start() -> None:
    """Inicia el monitor de seguridad como daemon thread."""
    global _started
    with _lock:
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

