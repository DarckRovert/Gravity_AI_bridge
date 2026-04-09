"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          GRAVITY AI - DATA GUARDIAN V9.0 PRO [Diamond-Tier Edition]          ║
║          Validación, reparación y saneamiento de archivos de datos           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import os
import re
import shutil
import glob
import logging
from datetime import datetime
from typing import Any

log = logging.getLogger("gravity.guardian")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Límites de seguridad ───────────────────────────────────────────────────────
MAX_HISTORY_MESSAGES = 2000      # Historial máximo antes de truncar
MAX_MESSAGE_CHARS    = 200_000   # Longitud máxima por mensaje (~50k tokens)
MAX_KNOWLEDGE_RULES  = 500       # Reglas máximas en _knowledge.json
MAX_RULE_CHARS       = 2_000     # Longitud máxima por regla
MAX_AUDIT_LINES      = 100_000   # Líneas máximas en el audit
MAX_AUDIT_FILE_MB    = 50        # Rotación si el archivo supera este tamaño
MAX_BACKUPS          = 3         # Máximo de backups por archivo (los más viejos se eliminan)

VALID_ROLES = {"system", "user", "assistant", "function", "tool"}


# ── Gestión de backups ─────────────────────────────────────────────────────────

def _backup(path: str) -> str:
    """
    Crea una copia de seguridad con timestamp.
    Mantiene solo MAX_BACKUPS backups por archivo (elimina los más viejos).
    Retorna la ruta del backup creado, o "" si falló.
    """
    ts     = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = f"{path}.bak_{ts}"
    try:
        shutil.copy2(path, backup)
    except Exception as e:
        log.warning(f"[Guardian] No se pudo hacer backup de {path}: {e}")
        return ""

    # Rotar: eliminar backups viejos si excede el límite
    pattern  = f"{path}.bak_*"
    existing = sorted(glob.glob(pattern))  # Orden cronológico por nombre
    while len(existing) > MAX_BACKUPS:
        oldest = existing.pop(0)
        try:
            os.unlink(oldest)
        except Exception:
            pass

    return backup


# ── Carga segura de JSON ───────────────────────────────────────────────────────

def _load_json_safe(path: str) -> tuple[Any, list[str]]:
    """
    Carga un archivo JSON capturando errores.
    Intenta recuperación parcial si el JSON está truncado.
    Retorna (data_o_None, lista_de_advertencias).
    """
    warnings = []
    if not os.path.exists(path):
        return None, []

    try:
        raw = open(path, "r", encoding="utf-8", errors="replace").read()
    except Exception as e:
        warnings.append(f"No se pudo leer {os.path.basename(path)}: {e}")
        return None, warnings

    if not raw.strip():
        warnings.append(f"{os.path.basename(path)} está vacío.")
        return None, warnings

    try:
        return json.loads(raw), warnings
    except json.JSONDecodeError as e:
        warnings.append(f"{os.path.basename(path)} JSON inválido en línea {e.lineno}: {e.msg}")
        # Recuperación parcial: buscar el último } o ] válido
        for end_char in ("}", "]"):
            idx = raw.rfind(end_char)
            if idx != -1:
                try:
                    recovered = json.loads(raw[:idx + 1])
                    warnings.append(f"Recuperación parcial exitosa (hasta posición {idx}).")
                    return recovered, warnings
                except Exception:
                    pass
        return None, warnings


# ── Validación de mensajes de historial ───────────────────────────────────────

def _is_valid_message(msg: Any) -> tuple[bool, str]:
    """Valida estructura de un mensaje de chat."""
    if not isinstance(msg, dict):
        return False, f"No es dict: {type(msg).__name__}"
    role = msg.get("role")
    if role not in VALID_ROLES:
        return False, f"role inválido: {repr(role)}"
    content = msg.get("content")
    if content is None:
        return False, "Falta 'content'"
    if not isinstance(content, (str, list)):
        return False, f"content debe ser str o list, es: {type(content).__name__}"
    if isinstance(content, str) and len(content) > MAX_MESSAGE_CHARS:
        return False, f"Mensaje demasiado largo: {len(content):,} chars"
    return True, ""


# ── Historial ─────────────────────────────────────────────────────────────────

def validate_history(history: list) -> tuple[list, list[str]]:
    """
    Valida y sanea una lista de mensajes de historial en memoria.
    - Elimina mensajes malformados.
    - Trunca mensajes excesivamente largos (conserva inicio + fin).
    - Limita cantidad total preservando el system prompt.
    Retorna (historia_saneada, warnings).
    """
    warnings = []
    if not isinstance(history, list):
        warnings.append(f"El historial no es una lista: {type(history).__name__}. Reseteando.")
        return [], warnings

    cleaned = []
    removed = 0

    for i, msg in enumerate(history):
        valid, reason = _is_valid_message(msg)
        if not valid:
            warnings.append(f"Mensaje [{i}] eliminado — {reason}")
            removed += 1
            continue

        content = msg.get("content", "")
        if isinstance(content, str) and len(content) > MAX_MESSAGE_CHARS:
            keep_start = int(MAX_MESSAGE_CHARS * 0.9)
            keep_end   = MAX_MESSAGE_CHARS - keep_start
            truncated  = (content[:keep_start]
                          + f"\n[...TRUNCADO {len(content)-MAX_MESSAGE_CHARS:,} chars...]\n"
                          + content[-keep_end:])
            msg = {**msg, "content": truncated}
            warnings.append(f"Mensaje [{i}] truncado: {len(content):,} → {MAX_MESSAGE_CHARS:,} chars")

        cleaned.append(msg)

    if len(cleaned) > MAX_HISTORY_MESSAGES:
        excess      = len(cleaned) - MAX_HISTORY_MESSAGES
        system_msgs = [m for m in cleaned if m.get("role") == "system"]
        other_msgs  = [m for m in cleaned if m.get("role") != "system"][excess:]
        cleaned     = system_msgs + other_msgs
        warnings.append(f"Historial truncado: {excess} mensajes antiguos eliminados.")

    if removed:
        warnings.append(f"Total mensajes eliminados por corrupción: {removed}")

    return cleaned, warnings


def load_history_file(path: str) -> tuple[list, list[str]]:
    """
    Carga un archivo de sesión JSON y valida su historial.
    Retorna (history_list, warnings).
    """
    warnings  = []
    data, w   = _load_json_safe(path)
    warnings += w

    if data is None:
        if os.path.exists(path):
            backup = _backup(path)
            if backup:
                warnings.append(f"Backup creado: {os.path.basename(backup)}")
        return [], warnings

    raw_history = data.get("history", [])
    if not isinstance(raw_history, list):
        warnings.append("El campo 'history' no es una lista. Usando historial vacío.")
        return [], warnings

    history, w2 = validate_history(raw_history)
    warnings   += w2
    return history, warnings


# ── Knowledge ─────────────────────────────────────────────────────────────────

def load_knowledge(path: str) -> tuple[dict, list[str]]:
    """
    Carga y valida _knowledge.json.
    Sanea reglas malformadas, largas o duplicadas.
    Retorna (knowledge_dict_sano, warnings).
    """
    warnings = []
    default  = {"persistent_rules": [], "version": "8.0"}

    if not os.path.exists(path):
        return default, warnings

    data, w   = _load_json_safe(path)
    warnings += w

    if data is None:
        backup = _backup(path)
        if backup:
            warnings.append(f"_knowledge.json corrupto — backup: {os.path.basename(backup)}")
        return default, warnings

    if not isinstance(data, dict):
        warnings.append("_knowledge.json no es un objeto JSON. Reseteando.")
        _backup(path)
        return default, warnings

    raw_rules = data.get("persistent_rules", [])
    if not isinstance(raw_rules, list):
        warnings.append("'persistent_rules' no es una lista. Reseteando reglas.")
        raw_rules = []

    clean_rules = []
    seen        = set()
    removed_r   = 0

    for i, rule in enumerate(raw_rules):
        if not isinstance(rule, str):
            warnings.append(f"Regla [{i}] eliminada: no es string ({type(rule).__name__})")
            removed_r += 1
            continue

        rule_stripped = rule.strip()
        if not rule_stripped:
            removed_r += 1
            continue

        if len(rule_stripped) > MAX_RULE_CHARS:
            rule_stripped = rule_stripped[:MAX_RULE_CHARS] + " [TRUNCADA]"
            warnings.append(f"Regla [{i}] truncada a {MAX_RULE_CHARS} chars")

        # Deduplicar por contenido normalizado
        key = re.sub(r'\s+', ' ', rule_stripped.lower())
        if key in seen:
            removed_r += 1
            continue
        seen.add(key)
        clean_rules.append(rule_stripped)

    if len(clean_rules) > MAX_KNOWLEDGE_RULES:
        excess      = len(clean_rules) - MAX_KNOWLEDGE_RULES
        clean_rules = clean_rules[excess:]
        warnings.append(f"Knowledge: {excess} reglas antiguas eliminadas (límite {MAX_KNOWLEDGE_RULES})")

    if removed_r:
        warnings.append(f"Knowledge: {removed_r} reglas corruptas o duplicadas eliminadas")

    data["persistent_rules"] = clean_rules
    return data, warnings


def save_knowledge(path: str, data: dict) -> tuple[bool, list[str]]:
    """
    Valida y guarda knowledge de forma atómica (.tmp → rename).
    Previene corrupción por escritura interrumpida.
    Retorna (exito, warnings).
    """
    warnings = []

    # Validación mínima antes de escribir
    if not isinstance(data, dict):
        return False, [f"save_knowledge: data no es dict: {type(data).__name__}"]

    rules = data.get("persistent_rules")
    if rules is not None and not isinstance(rules, list):
        warnings.append("persistent_rules no era lista — reseteado a []")
        data = {**data, "persistent_rules": []}

    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
        return True, warnings
    except Exception as e:
        warnings.append(f"Error escribiendo knowledge: {e}")
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        return False, warnings




# ── Audit Log ─────────────────────────────────────────────────────────────────

def _audit_log_has_corruption(path: str) -> bool:
    """
    Comprobación RÁPIDA de integridad del audit log.
    Verifica solo la última línea no vacía.
    O(1) en lugar de O(n). Solo si hay problema real se llama repair_audit_log.
    """
    try:
        size_mb = os.path.getsize(path) / (1024 * 1024)
        if size_mb > MAX_AUDIT_FILE_MB:
            return True  # Necesita rotación

        # Leer solo el final del archivo (últimos 4KB)
        with open(path, "rb") as f:
            f.seek(max(0, os.path.getsize(path) - 4096))
            tail = f.read().decode("utf-8", errors="replace")

        lines = [l.strip() for l in tail.splitlines() if l.strip()]
        if not lines:
            return False  # Vacío = OK

        last_line = lines[-1]
        entry = json.loads(last_line)
        if not isinstance(entry, dict) or "timestamp" not in entry:
            return True
        datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
        return False  # Última línea válida → asumimos el resto también
    except Exception:
        return True  # Cualquier error → marcar como corrupto


def repair_audit_log(path: str) -> tuple[int, int, list[str]]:
    """
    Repara _audit_log.jsonl línea a línea.
    SOLO llamar cuando _audit_log_has_corruption() retorna True.
    Retorna (lineas_ok, lineas_eliminadas, warnings).
    """
    warnings = []
    if not os.path.exists(path):
        return 0, 0, warnings

    size_mb = os.path.getsize(path) / (1024 * 1024)
    if size_mb > MAX_AUDIT_FILE_MB:
        backup = _backup(path)
        warnings.append(
            f"Audit log ({size_mb:.1f} MB) supera {MAX_AUDIT_FILE_MB} MB. "
            f"Rotado → {os.path.basename(backup)}"
        )
        open(path, "w").close()
        return 0, 0, warnings

    try:
        raw = open(path, "r", encoding="utf-8", errors="replace").readlines()
    except Exception as e:
        warnings.append(f"No se pudo leer audit_log: {e}")
        return 0, 0, warnings

    ok_lines      = []
    removed_count = 0

    for i, line in enumerate(raw):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            if not isinstance(entry, dict):
                raise ValueError("No es dict")
            if "timestamp" not in entry:
                raise ValueError("Sin timestamp")
            datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
            ok_lines.append(json.dumps(entry, ensure_ascii=False))
        except Exception as e:
            removed_count += 1
            if removed_count <= 5:
                warnings.append(f"Audit línea {i+1} eliminada: {str(e)[:60]}")

    if len(ok_lines) > MAX_AUDIT_LINES:
        excess   = len(ok_lines) - MAX_AUDIT_LINES
        ok_lines = ok_lines[excess:]
        warnings.append(f"Audit: {excess} entradas antiguas descartadas (límite {MAX_AUDIT_LINES:,})")

    if removed_count > 0:
        backup = _backup(path)
        if backup:
            warnings.append(f"Audit backup creado: {os.path.basename(backup)}")

    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write("\n".join(ok_lines))
            if ok_lines:
                f.write("\n")
        os.replace(tmp, path)
    except Exception as e:
        warnings.append(f"No se pudo escribir audit reparado: {e}")
        if os.path.exists(tmp):
            os.unlink(tmp)

    return len(ok_lines), removed_count, warnings


# ── Startup Check ─────────────────────────────────────────────────────────────

def startup_check(base_dir: str = BASE_DIR) -> tuple[dict, list[str]]:
    """
    Chequeo de integridad al arranque del sistema.

    Cambios vs V1:
      - Carga knowledge UNA sola vez y retorna el objeto (evita doble lectura).
      - repair_audit_log es LAZY: solo actúa si _audit_log_has_corruption() == True.
      - Backups se auto-rotan (máximo MAX_BACKUPS por archivo).

    Retorna (knowledge_dict, lista_de_advertencias).
    El llamador usa el knowledge_dict directamente para construir el system prompt.
    """
    all_warnings = []

    # ── 1. Knowledge JSON (lectura única) ────────────────────────────────────
    kb_path = os.path.join(base_dir, "_knowledge.json")
    kb, w   = load_knowledge(kb_path)
    all_warnings += w

    # ── 2. Audit JSONL (lazy: comprobación O(1) antes de reparar) ────────────
    audit_path = os.path.join(base_dir, "_audit_log.jsonl")
    if os.path.exists(audit_path) and _audit_log_has_corruption(audit_path):
        ok, removed, w = repair_audit_log(audit_path)
        all_warnings += w
        if removed:
            all_warnings.append(
                f"Audit log reparado: {ok} entradas válidas, {removed} corruptas eliminadas."
            )

    return kb, all_warnings
