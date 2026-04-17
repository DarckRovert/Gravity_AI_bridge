"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         GRAVITY AI — GAME SERVER MANAGER V10.0                               ║
║         Gestión de servidores de juegos desde el Bridge                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

Soporta actualmente:
  - WoW Vanilla vía MaNGOS / vMaNGOS (mangosd.exe + realmd.exe)
    Ruta por defecto: F:\\Project_Anarchy_Core\\MaNGOS
  - Extensible a cualquier servidor con proceso + log en disco

Endpoints expuestos por bridge_server:
  GET  /v1/gameserver/status          — Estado de todos los servidores
  POST /v1/gameserver/start           — Iniciar servidor {"server": "wow_vanilla"}
  POST /v1/gameserver/stop            — Detener servidor
  POST /v1/gameserver/restart         — Reiniciar servidor
  POST /v1/gameserver/command         — Enviar comando GM (si SOAP configurado)
  GET  /v1/gameserver/log             — Últimas N líneas del log
  GET  /v1/gameserver/players         — Jugadores online (requiere pymysql)
"""

import os
import json
import time
import subprocess
import threading
import logging
from datetime import datetime
from typing import Optional
import hashlib

log = logging.getLogger("gravity.gameserver")

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE   = os.path.join(BASE_DIR, "config.yaml")

# ── Configuración por Defecto ──────────────────────────────────────────────────

DEFAULT_SERVERS: dict = {
    "wow_vanilla": {
        "enabled":              True,
        "display_name":         "WoW Vanilla (MaNGOS)",
        "type":                 "mangos",
        "server_dir":           r"F:\Project_Anarchy_Core\MaNGOS",
        "worldserver_exe":      "mangosd.exe",
        "realmd_exe":           "realmd.exe",
        "mysql_start_bat":      r"F:\Project_Anarchy_Core\MaNGOS\Start MySQL.bat",
        "mysql_stop_bat":       r"F:\Project_Anarchy_Core\MaNGOS\Stop MySQL.bat",
        "log_file":             r"F:\Project_Anarchy_Core\MaNGOS\logs\mangosd.log",
        "auto_restart":         True,
        "restart_delay_seconds": 15,
        # Conexión a MySQL para players online — dejar vacío si no aplica
        "db_host":   "127.0.0.1",
        "db_port":   3306,
        "db_name":   "characters",
        "db_user":   "mangos",
        "db_pass":   "",
    }
}

# pymysql opcional — si no está instalado, la función de jugadores retorna aviso
try:
    import pymysql
    _PYMYSQL_OK = True
except ImportError:
    _PYMYSQL_OK = False

# ── Estado Global ──────────────────────────────────────────────────────────────

_processes: dict[str, dict] = {}  # {server_id: {proc_world, proc_realm, status, ...}}
_lock = threading.Lock()
_watchdog_threads: dict[str, threading.Thread] = {}
_started = False


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _load_config() -> dict:
    """Carga la configuración de game_servers desde config.yaml si existe."""
    try:
        import yaml  # type: ignore
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        return cfg.get("game_servers", DEFAULT_SERVERS)
    except Exception:
        return DEFAULT_SERVERS


def _is_running(proc: Optional[subprocess.Popen]) -> bool:
    """Devuelve True si el proceso está vivo."""
    if proc is None:
        return False
    return proc.poll() is None


def _tail_log(log_path: str, lines: int = 100) -> list[str]:
    """Lee las últimas N líneas de un archivo de log."""
    if not os.path.exists(log_path):
        return [f"[Log no encontrado: {log_path}]"]
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
        return [l.rstrip() for l in all_lines[-lines:]]
    except Exception as e:
        return [f"[Error leyendo log: {e}]"]


# ── Control de Procesos ────────────────────────────────────────────────────────

def _start_server(server_id: str, cfg: dict) -> dict:
    """Inicia los procesos de un servidor. Devuelve el estado resultante."""
    server_dir  = cfg.get("server_dir", "")
    world_exe   = os.path.join(server_dir, cfg.get("worldserver_exe", "mangosd.exe"))
    realm_exe   = os.path.join(server_dir, cfg.get("realmd_exe",     "realmd.exe"))
    mysql_bat   = cfg.get("mysql_start_bat", "")

    # 0. Arrancar MySQL primero si hay bat configurado
    if mysql_bat and os.path.exists(mysql_bat):
        try:
            subprocess.Popen(
                ["cmd.exe", "/c", mysql_bat],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=os.path.dirname(mysql_bat),
            )
            log.info(f"[GameServer] MySQL arrancado para {server_id}")
            time.sleep(3)  # Esperar a que MySQL inicie
        except Exception as e:
            log.warning(f"[GameServer] No se pudo arrancar MySQL: {e}")

    procs: dict = {"world": None, "realm": None}
    errors: list[str] = []

    # 1. Realm server (autenticación)
    if os.path.exists(realm_exe):
        try:
            procs["realm"] = subprocess.Popen(
                [realm_exe],
                cwd=server_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            log.info(f"[GameServer] realmd.exe iniciado (PID {procs['realm'].pid})")
            time.sleep(2)
        except Exception as e:
            errors.append(f"realmd: {e}")
    else:
        errors.append(f"realmd.exe no encontrado en {realm_exe}")

    # 2. World server (juego)
    if os.path.exists(world_exe):
        try:
            procs["world"] = subprocess.Popen(
                [world_exe],
                cwd=server_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            log.info(f"[GameServer] mangosd.exe iniciado (PID {procs['world'].pid})")
        except Exception as e:
            errors.append(f"mangosd: {e}")
    else:
        errors.append(f"mangosd.exe no encontrado en {world_exe}")

    state = {
        "status":       "running" if not errors else "partial_error",
        "started_at":   _now(),
        "errors":       errors,
        "world_pid":    procs["world"].pid if procs["world"] else None,
        "realm_pid":    procs["realm"].pid if procs["realm"] else None,
        "_world_proc":  procs["world"],
        "_realm_proc":  procs["realm"],
        "cfg":          cfg,
        "display_name": cfg.get("display_name", server_id),
    }

    with _lock:
        _processes[server_id] = state

    # Iniciar watchdog si auto_restart está activo
    if cfg.get("auto_restart", True):
        _start_watchdog(server_id)

    return _public_state(state)


def _stop_server(server_id: str) -> dict:
    """Detiene los procesos de un servidor."""
    with _lock:
        state = _processes.get(server_id)

    if not state:
        return {"ok": False, "error": f"Servidor '{server_id}' no encontrado o no iniciado."}

    for key in ("_world_proc", "_realm_proc"):
        proc = state.get(key)
        if _is_running(proc):
            try:
                proc.terminate()
                proc.wait(timeout=10)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

    # Detener MySQL si corresponde
    mysql_bat = state.get("cfg", {}).get("mysql_stop_bat", "")
    if mysql_bat and os.path.exists(mysql_bat):
        try:
            subprocess.Popen(["cmd.exe", "/c", mysql_bat], creationflags=subprocess.CREATE_NEW_CONSOLE)
        except Exception:
            pass

    with _lock:
        if server_id in _processes:
            _processes[server_id]["status"]     = "stopped"
            _processes[server_id]["stopped_at"] = _now()
            _processes[server_id]["_world_proc"] = None
            _processes[server_id]["_realm_proc"] = None

    return {"ok": True, "server": server_id, "status": "stopped"}


def _start_watchdog(server_id: str) -> None:
    """Daemon que reinicia el servidor si cae inesperadamente."""
    if server_id in _watchdog_threads \
            and _watchdog_threads[server_id].is_alive():
        return

    def _watch():
        while True:
            time.sleep(10)
            with _lock:
                state = _processes.get(server_id)
            if not state or state.get("status") == "stopped":
                break  # Apagado manualmente — no reiniciar

            world_proc = state.get("_world_proc")
            realm_proc = state.get("_realm_proc")
            world_died = not _is_running(world_proc) and world_proc is not None
            realm_died = not _is_running(realm_proc) and realm_proc is not None

            if world_died or realm_died:
                delay = state.get("cfg", {}).get("restart_delay_seconds", 15)
                log.warning(
                    f"[GameServer Watchdog] {server_id} cayó. "
                    f"Reiniciando en {delay}s..."
                )
                time.sleep(delay)
                cfg = state.get("cfg", {})
                _start_server(server_id, cfg)
                break  # El nuevo _start_server inicia un watchdog fresco

    t = threading.Thread(
        target=_watch,
        name=f"GravityWatchdog_{server_id}",
        daemon=True,
    )
    _watchdog_threads[server_id] = t
    t.start()


# ── Consulta de Jugadores (MySQL) ──────────────────────────────────────────────

def _get_players_online(server_id: str) -> list[dict]:
    """Consulta la BD de characters para devolver jugadores online."""
    if not _PYMYSQL_OK:
        return [{"error": "pymysql no instalado. Ejecuta: pip install pymysql"}]

    with _lock:
        state = _processes.get(server_id, {})
    cfg = state.get("cfg", DEFAULT_SERVERS.get(server_id, {}))

    try:
        conn = pymysql.connect(
            host    = cfg.get("db_host", "127.0.0.1"),
            port    = int(cfg.get("db_port", 3306)),
            user    = cfg.get("db_user", "mangos"),
            password= cfg.get("db_pass", ""),
            database= cfg.get("db_name", "characters"),
            connect_timeout=3,
        )
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("""
                SELECT
                    name              AS player,
                    level             AS level,
                    race              AS race_id,
                    class             AS class_id,
                    zone              AS zone_id,
                    online            AS online
                FROM characters
                WHERE online = 1
                ORDER BY name
                LIMIT 100
            """)
            rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return [{"error": str(e)}]


# ── Estado Público (sin objetos de proceso) ────────────────────────────────────

def _public_state(state: dict) -> dict:
    """Extrae la información serializable de un estado de servidor."""
    world_proc = state.get("_world_proc")
    realm_proc = state.get("_realm_proc")
    return {
        "status":       state.get("status", "unknown"),
        "display_name": state.get("display_name", "?"),
        "started_at":   state.get("started_at"),
        "stopped_at":   state.get("stopped_at"),
        "world_pid":    world_proc.pid if _is_running(world_proc) else None,
        "realm_pid":    realm_proc.pid if _is_running(realm_proc) else None,
        "world_alive":  _is_running(world_proc),
        "realm_alive":  _is_running(realm_proc),
        "errors":       state.get("errors", []),
        "auto_restart": state.get("cfg", {}).get("auto_restart", True),
    }


# ── API Pública ────────────────────────────────────────────────────────────────

def get_all_status() -> dict:
    """Devuelve el estado de todos los servidores configurados."""
    servers_cfg = _load_config()
    result: dict = {}

    for sid, cfg in servers_cfg.items():
        with _lock:
            state = _processes.get(sid)
        if state:
            result[sid] = _public_state(state)
        else:
            # Servidor configurado pero no iniciado
            result[sid] = {
                "status":       "stopped",
                "display_name": cfg.get("display_name", sid),
                "world_pid":    None,
                "realm_pid":    None,
                "world_alive":  False,
                "realm_alive":  False,
                "errors":       [],
                "auto_restart": cfg.get("auto_restart", True),
            }

    return {
        "servers":      result,
        "pymysql_available": _PYMYSQL_OK,
        "timestamp":    _now(),
    }


def start(server_id: str) -> dict:
    """Inicia un servidor por su ID."""
    servers_cfg = _load_config()
    cfg = servers_cfg.get(server_id)
    if not cfg:
        return {"ok": False, "error": f"Servidor '{server_id}' no existe en la configuración."}

    with _lock:
        state = _processes.get(server_id)
    if state and state.get("status") == "running":
        world_ok = _is_running(state.get("_world_proc"))
        realm_ok = _is_running(state.get("_realm_proc"))
        if world_ok or realm_ok:
            return {"ok": False, "error": f"'{server_id}' ya está corriendo."}

    return {"ok": True, **_start_server(server_id, cfg)}


def stop(server_id: str) -> dict:
    """Detiene un servidor por su ID."""
    return _stop_server(server_id)


def restart(server_id: str) -> dict:
    """Reinicia un servidor."""
    stop_result = _stop_server(server_id)
    time.sleep(3)
    return start(server_id)


def get_log(server_id: str, lines: int = 100) -> dict:
    """Devuelve las últimas líneas del log del servidor."""
    servers_cfg = _load_config()
    cfg = servers_cfg.get(server_id, {})
    log_path = cfg.get("log_file", "")
    return {
        "server":   server_id,
        "log_file": log_path,
        "lines":    _tail_log(log_path, lines),
    }


def get_players(server_id: str) -> dict:
    """Devuelve la lista de jugadores online."""
    players = _get_players_online(server_id)
    return {
        "server":  server_id,
        "count":   len([p for p in players if "error" not in p]),
        "players": players,
    }


def send_command(server_id: str, command: str) -> dict:
    """
    Envía un comando al servidor.
    MaNGOS no tiene SOAP habilitado por defecto. Por ahora devuelve
    instrucción de ejecutar el comando directamente en la consola del servidor.
    Extensible a SOAP/TCP en versiones futuras.
    """
    return {
        "ok":      False,
        "server":  server_id,
        "command": command,
        "note":    (
            "Ejecución directa de comandos GM requiere SOAP habilitado en mangosd.conf "
            "(SOAPEnabled=1, SOAPPort=7878). Activa esa opción y reinicia el servidor. "
            "Por ahora, ejecuta el comando directamente en la ventana de la consola del worldserver."
        ),
    }

def register_account(server_id: str, username: str, password: str) -> dict:
    """Crea una nueva cuenta usando SRP-6a (vMaNGOS) o SHA1 (MaNGOS clásico)."""
    if not _PYMYSQL_OK:
        return {"ok": False, "error": "pymysql no instalado. Ejecuta: pip install pymysql"}

    servers_cfg = _load_config()
    cfg = servers_cfg.get(server_id, {})
    if not cfg:
        return {"ok": False, "error": f"Servidor {server_id} inexistente."}

    db_auth = cfg.get("db_name_auth", "realmd")

    try:
        conn = pymysql.connect(
            host            = cfg.get("db_host", "127.0.0.1"),
            port            = int(cfg.get("db_port", 3306)),
            user            = cfg.get("db_user", "mangos"),
            password        = cfg.get("db_pass", ""),
            database        = db_auth,
            connect_timeout = 3,
        )
        with conn.cursor() as cur:
            # 1. Verificar si ya existe
            cur.execute("SELECT id FROM account WHERE username = %s LIMIT 1", (username.upper(),))
            if cur.fetchone():
                conn.close()
                return {"ok": False, "error": "Ese nombre de usuario ya está tomado."}

            # 2. Detectar modo (SRP-6a vs SHA1)
            # vMaNGOS tiene columnas 'v' y 's'
            cur.execute("SHOW COLUMNS FROM account LIKE 'v'")
            is_srp = cur.fetchone() is not None

            if is_srp:
                # Protocolo SRP-6a para vMaNGOS/Trinity
                N = 0x894B645E89E1535BBDAD5B8B290650530801B18EBFBF5E8FAB3C82872A3E9BB7
                g = 7
                s_bytes = os.urandom(32)
                h1      = hashlib.sha1(f"{username.upper()}:{password.upper()}".encode("utf-8")).digest()
                x_bytes = hashlib.sha1(s_bytes + h1).digest()
                x       = int.from_bytes(x_bytes, 'little')
                v       = pow(g, x, N)

                v_hex = v.to_bytes(32, 'little').hex().upper()
                s_hex = s_bytes.hex().upper()

                cur.execute("""
                    INSERT INTO account (username, v, s, gmlevel, sessionkey, token_key, os, platform)
                    VALUES (%s, %s, %s, 0, '', '', '', '')
                """, (username.upper(), v_hex, s_hex))
            else:
                # Fallback SHA1 (MaNGOS clásico)
                raw_str      = f"{username.upper()}:{password.upper()}"
                sha_pass_hash = hashlib.sha1(raw_str.encode("utf-8")).hexdigest().upper()
                cur.execute("""
                    INSERT INTO account (username, sha_pass_hash, v, s, sessionkey)
                    VALUES (%s, %s, '0', '0', '')
                """, (username.upper(), sha_pass_hash))

            conn.commit()

        conn.close()
        return {"ok": True, "message": f"Cuenta '{username}' registrada correctamente en el servidor."}
    except Exception as e:
        log.error(f"Error registrando cuenta: {e}")
        return {"ok": False, "error": str(e)}

def expose_wan(server_id: str, public_address: str) -> dict:
    """Configura el Firewall local y reescribe el realmlist DB en MySQL."""
    servers_cfg = _load_config()
    cfg = servers_cfg.get(server_id, {})
    
    if public_address in ["127.0.0.1", "localhost", "0.0.0.0"]:
        return {"ok": False, "error": "Debes especificar tu IP pública o dominio DDNS válido, no localhost."}
        
    try:
        log.info(f"Aplicando reglas Firewall para WoW (8085, 3724)...")
        # Inyectando silenciosamente reglas de firewall por CMD, requiere ADMIN
        subprocess.run(
            ["netsh", "advfirewall", "firewall", "add", "rule", 
             "name=Gravity_WoW_MANGOS", "dir=in", "action=allow", 
             "protocol=TCP", "localport=8085,3724"],
            capture_output=True, check=False, creationflags=subprocess.CREATE_NO_WINDOW
        )
    except Exception as e:
        return {"ok": False, "error": f"Fallo añadiendo reglas Firewall. Requieres abrir Bridge como Admin: {e}"}
        
    if _PYMYSQL_OK:
        try:
            db_auth = cfg.get("db_name_auth", "realmd")
            conn = pymysql.connect(
                host    = cfg.get("db_host", "127.0.0.1"),
                port    = int(cfg.get("db_port", 3306)),
                user    = cfg.get("db_user", "mangos"),
                password= cfg.get("db_pass", ""),
                database= db_auth,
                connect_timeout=3,
            )
            with conn.cursor() as cur:
                cur.execute("UPDATE realmlist SET address = %s WHERE id = 1", (public_address,))
                conn.commit()
            conn.close()
        except Exception as e:
            return {"ok": False, "error": f"Firewall aplicado pero error actualizando 'realmlist' SQL: {e}"}
    else:
        log.warning("pymysql no disponible. Firewall modificado pero no se alteró el MySQL.")
        
    return {
        "ok": True, 
        "message": f"Servidor configurado. Realm apuntando hacia: {public_address} y puertos TCP abiertos en SO."
    }
