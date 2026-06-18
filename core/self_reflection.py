"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — SELF REFLECTION ENGINE V16.0 PRO [Autonomous Edition]         ║
║                                                                              ║
║  Gravity observa su propio comportamiento histórico y propone mejoras.      ║
║                                                                              ║
║  Ciclo:                                                                      ║
║    1. Escanea _audit_log.jsonl buscando errores recurrentes                 ║
║    2. Analiza módulos con 0 actividad en N días (módulos idle)              ║
║    3. Verifica configuración contra estado real del sistema                  ║
║    4. Genera informe de "deuda técnica + oportunidades detectadas"           ║
║    5. Si encuentra bug reproducible → guarda propuesta .patch en            ║
║       _self_patches/<timestamp>_<module>.patch + metadata.json              ║
║                                                                              ║
║  Restricciones de seguridad:                                                 ║
║    ▸ Solo propone, NUNCA aplica cambios automáticamente                     ║
║    ▸ Todos los parches requieren aprobación humana vía HITL                 ║
║    ▸ Lee código fuente pero no lo modifica directamente                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import re
import threading
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from core.logger import log

BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT_LOG_PATH: str = os.path.join(BASE_DIR, "_audit_log.jsonl")
PATCHES_DIR: str = os.path.join(BASE_DIR, "_self_patches")
KNOWLEDGE_FILE: str = os.path.join(BASE_DIR, "_knowledge.json")

# Ciclo de introspección por defecto (horas)
REFLECTION_INTERVAL_H: float = 6.0

_lock = threading.RLock()
_started: bool = False

# Estado observable desde el dashboard
_state: Dict[str, Any] = {
    "running":       False,
    "last_run_utc":  None,
    "next_run_utc":  None,
    "last_report":   None,
    "patches_pending": 0,
    "issues_found":  0,
    "cycles_done":   0,
}


# ── Utilidades ────────────────────────────────────────────────────────────────

def _safe_read_jsonl(path: str, max_lines: int = 5000) -> List[Dict]:
    """Lee las últimas max_lines líneas de un archivo JSONL de forma segura."""
    result: List[Dict] = []
    if not os.path.isfile(path):
        return result
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        for line in lines[-max_lines:]:
            line = line.strip()
            if not line:
                continue
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    except Exception as e:
        log.warning(f"[SelfReflection] Error leyendo {path}: {e}")
    return result


def _read_file_safe(path: str, max_bytes: int = 50_000) -> str:
    """Lee un archivo de código fuente de forma segura."""
    if not os.path.isfile(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(max_bytes)
        return content
    except Exception:
        return ""


# ── Análisis del Audit Log ────────────────────────────────────────────────────

def _analyze_audit_log(days: int = 7) -> Dict[str, Any]:
    """
    Analiza el audit log buscando patrones de error.
    Retorna:
      - error_counts: módulos con más errores
      - recurrent_errors: mensajes que aparecen 3+ veces
      - idle_modules: módulos sin actividad en N días
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    entries = _safe_read_jsonl(AUDIT_LOG_PATH)

    error_counts: Counter = Counter()
    recurrent_errors: List[str] = []
    error_messages: Counter = Counter()
    active_modules: set = set()

    for entry in entries:
        ts = entry.get("timestamp", entry.get("saved_at", ""))
        if ts < cutoff:
            continue

        level = str(entry.get("level", "")).upper()
        provider = entry.get("provider", entry.get("module", "unknown"))
        if provider:
            active_modules.add(provider)

        if level in ("ERROR", "CRITICAL"):
            error_counts[provider] += 1
            msg = str(entry.get("data", entry.get("message", "")))[:200]
            if msg:
                error_messages[msg] += 1

    # Mensajes que aparecen 3+ veces = error recurrente
    recurrent_errors = [msg for msg, cnt in error_messages.items() if cnt >= 3]

    # Módulos core conocidos que deberian tener actividad
    known_modules = {
        "content_scheduler", "bounty_hunter", "security_monitor",
        "image_queue", "video_pipeline", "provider_manager",
    }
    idle_modules = known_modules - {m.lower().replace("core.", "") for m in active_modules}

    return {
        "error_counts":     dict(error_counts.most_common(10)),
        "recurrent_errors": recurrent_errors[:5],
        "idle_modules":     list(idle_modules),
        "active_modules":   list(active_modules)[:20],
        "period_days":      days,
    }


# ── Análisis de configuración ─────────────────────────────────────────────────

def _analyze_config() -> List[Dict[str, str]]:
    """
    Verifica configuración en config.yaml vs estado real del sistema.
    Retorna lista de inconsistencias detectadas.
    """
    issues: List[Dict[str, str]] = []
    try:
        from core.config_manager import config

        # Verificar scheduler
        scheduler = config.get("scheduler", {})
        if not scheduler.get("enabled", False):
            issues.append({
                "severity": "WARNING",
                "module":   "content_scheduler",
                "issue":    "Scheduler deshabilitado en config — 0 videos se producirán automáticamente",
                "suggestion": "Activar scheduler.enabled: true en config.yaml si se desea producción autónoma"
            })

        # Verificar daily cost limit
        cost_limit = config.get("cost.daily_limit_usd", 0)
        if cost_limit <= 0:
            issues.append({
                "severity": "WARNING",
                "module":   "cost_tracker",
                "issue":    "Límite de costo diario no configurado o en cero",
                "suggestion": "Configurar cost.daily_limit_usd en config.yaml para evitar gastos no controlados"
            })

        # Verificar ComfyUI
        comfy_enabled = config.get("comfyui.enabled", False)
        comfy_path = os.path.join(BASE_DIR, "_integrations", "ComfyUI_windows_portable")
        if comfy_enabled and not os.path.isdir(comfy_path):
            issues.append({
                "severity": "ERROR",
                "module":   "comfyui",
                "issue":    "comfyui.enabled=true pero la instalación no existe en _integrations/ComfyUI_windows_portable",
                "suggestion": "Deshabilitar comfyui.enabled o instalar ComfyUI en la ruta esperada"
            })

        # Verificar providers
        providers_cfg = config.get("providers", {})
        if not providers_cfg:
            issues.append({
                "severity": "WARNING",
                "module":   "provider_manager",
                "issue":    "No hay proveedores de IA configurados en config.yaml",
                "suggestion": "Configurar al menos un proveedor local (LM Studio, Ollama) o cloud (OpenRouter)"
            })

    except Exception as e:
        issues.append({
            "severity": "ERROR",
            "module":   "config_manager",
            "issue":    f"Error leyendo configuración: {e}",
            "suggestion": "Verificar que config.yaml existe y tiene formato YAML válido"
        })

    return issues


# ── Generación de parches ─────────────────────────────────────────────────────

def _save_patch_proposal(
    module_name: str,
    issue_description: str,
    patch_content: str,
    metadata: Optional[Dict] = None,
) -> str:
    """
    Guarda una propuesta de parche en _self_patches/.
    Retorna la ruta del archivo de metadata creado.
    """
    os.makedirs(PATCHES_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    slug = re.sub(r"[^a-zA-Z0-9_]", "_", module_name)[:30]

    patch_file   = os.path.join(PATCHES_DIR, f"{ts}_{slug}.patch")
    meta_file    = os.path.join(PATCHES_DIR, f"{ts}_{slug}_meta.json")

    try:
        with open(patch_file, "w", encoding="utf-8") as f:
            f.write(patch_content)

        meta = {
            "id":          f"{ts}_{slug}",
            "module":      module_name,
            "ts":          datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "issue":       issue_description,
            "patch_file":  patch_file,
            "status":      "pending",   # pending | approved | rejected | applied
            "applied_ts":  None,
            **(metadata or {}),
        }
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        log.info(f"[SelfReflection] Parche guardado: {patch_file}")
        return meta_file
    except Exception as e:
        log.error(f"[SelfReflection] Error guardando parche: {e}")
        return ""


def _count_pending_patches() -> int:
    """Cuenta los parches pendientes de aprobación."""
    if not os.path.isdir(PATCHES_DIR):
        return 0
    count = 0
    for fname in os.listdir(PATCHES_DIR):
        if fname.endswith("_meta.json"):
            try:
                fpath = os.path.join(PATCHES_DIR, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                if meta.get("status") == "pending":
                    count += 1
            except Exception:
                pass
    return count


# ── Ciclo de introspección completo ──────────────────────────────────────────

def run_reflection_cycle() -> Dict[str, Any]:
    """
    Ejecuta un ciclo completo de auto-introspección.
    Retorna el informe generado.
    """
    with _lock:
        _state["running"] = True

    start_ts = time.time()
    report: Dict[str, Any] = {
        "ts":          datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "audit_analysis": {},
        "config_issues":  [],
        "patches_generated": [],
        "opportunities":  [],
        "summary":        "",
    }

    log.info("[SelfReflection] Iniciando ciclo de auto-introspección...")

    try:
        # 1. Análisis del audit log
        audit = _analyze_audit_log(days=7)
        report["audit_analysis"] = audit

        # 2. Análisis de configuración
        config_issues = _analyze_config()
        report["config_issues"] = config_issues

        # 3. Detectar oportunidades (módulos idle con alto potencial)
        opportunities: List[str] = []
        idle = audit.get("idle_modules", [])
        for mod in idle:
            if mod == "bounty_hunter":
                opportunities.append(
                    "bounty_hunter inactivo — potencial de ingresos freelance no aprovechado"
                )
            elif mod == "content_scheduler":
                opportunities.append(
                    "content_scheduler inactivo — producción autónoma de contenido detenida"
                )
        report["opportunities"] = opportunities

        # 4. Persistir patrones detectados
        try:
            from core.strategic_memory import upsert_pattern, record_decision, CAT_SYSTEM, CAT_EVOLUTION
            for mod, count in audit.get("error_counts", {}).items():
                if count >= 3:
                    upsert_pattern(f"module_error:{mod}", str(count))

            for err in audit.get("recurrent_errors", []):
                upsert_pattern(f"recurrent_error", err[:100])

            # 5. Registrar la reflexión como decisión estratégica
            n_issues = len(config_issues) + len(audit.get("recurrent_errors", []))
            if n_issues > 0:
                record_decision(
                    category=CAT_SYSTEM,
                    title=f"Auto-introspección: {n_issues} problema(s) detectado(s)",
                    description=f"Ciclo de reflexión completado. Módulos idle: {idle}. "
                                f"Errores recurrentes: {len(audit.get('recurrent_errors', []))}. "
                                f"Problemas de config: {len(config_issues)}.",
                    rationale="Ciclo periódico de auto-análisis del sistema",
                    action_taken="Informe generado. Parches propuestos si aplica.",
                    metadata={"cycle_duration_s": round(time.time() - start_ts, 2)},
                )
        except Exception as e:
            log.warning(f"[SelfReflection] Error persistiendo patrones: {e}")

        # 6. Resumen textual
        total_issues = len(config_issues) + len(audit.get("recurrent_errors", []))
        total_patches = _count_pending_patches()
        report["summary"] = (
            f"Ciclo completado en {round(time.time() - start_ts, 1)}s. "
            f"Problemas detectados: {total_issues}. "
            f"Módulos idle: {len(idle)}. "
            f"Parches pendientes de aprobación: {total_patches}. "
            f"Oportunidades: {len(opportunities)}."
        )

        with _lock:
            _state["last_report"]      = report
            _state["issues_found"]     = total_issues
            _state["patches_pending"]  = total_patches
            _state["cycles_done"]     += 1
            _state["last_run_utc"]     = report["ts"]

        log.info(f"[SelfReflection] {report['summary']}")

    except Exception as e:
        log.error(f"[SelfReflection] Error en ciclo de reflexión: {e}")
        report["error"] = str(e)
    finally:
        with _lock:
            _state["running"] = False

    return report


# ── Gestión de parches ────────────────────────────────────────────────────────

def get_pending_patches() -> List[Dict[str, Any]]:
    """Retorna lista de parches pendientes de aprobación."""
    if not os.path.isdir(PATCHES_DIR):
        return []
    patches: List[Dict[str, Any]] = []
    for fname in sorted(os.listdir(PATCHES_DIR), reverse=True):
        if fname.endswith("_meta.json"):
            try:
                fpath = os.path.join(PATCHES_DIR, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                if meta.get("status") == "pending":
                    patches.append(meta)
            except Exception:
                pass
    return patches


def approve_patch(patch_id: str) -> Dict[str, Any]:
    """
    Aprueba y aplica un parche propuesto.
    Crea backup .bak del archivo original antes de aplicar.
    """
    if not os.path.isdir(PATCHES_DIR):
        return {"ok": False, "error": "Directorio de parches no existe"}

    meta_file = os.path.join(PATCHES_DIR, f"{patch_id}_meta.json")
    if not os.path.isfile(meta_file):
        return {"ok": False, "error": f"Parche {patch_id} no encontrado"}

    try:
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)

        if meta.get("status") != "pending":
            return {"ok": False, "error": f"Parche ya procesado: {meta.get('status')}"}

        patch_file = meta.get("patch_file", "")
        if not os.path.isfile(patch_file):
            return {"ok": False, "error": "Archivo .patch no encontrado"}

        # Leer el parche
        with open(patch_file, "r", encoding="utf-8") as f:
            patch_content = f.read()

        # Extraer archivo objetivo del parche (formato diff estándar: --- a/path)
        target_match = re.search(r'^--- a/(.+)$', patch_content, re.MULTILINE)
        if not target_match:
            return {"ok": False, "error": "Formato de parche inválido — no se encontró archivo objetivo"}

        target_rel = target_match.group(1).strip()
        target_abs = os.path.join(BASE_DIR, target_rel)

        if not os.path.isfile(target_abs):
            return {"ok": False, "error": f"Archivo objetivo no existe: {target_abs}"}

        # Crear backup
        backup_path = target_abs + f".bak.{patch_id}"
        with open(target_abs, "r", encoding="utf-8") as f:
            original = f.read()
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(original)

        # Aplicar usando patch simple (línea por línea diff unificado)
        try:
            import subprocess
            result = subprocess.run(
                ["patch", "--no-backup-if-mismatch", "-p1", "-i", patch_file],
                cwd=BASE_DIR,
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                # Restaurar backup si falló
                with open(target_abs, "w", encoding="utf-8") as f:
                    f.write(original)
                return {"ok": False, "error": f"patch falló: {result.stderr[:500]}"}
        except FileNotFoundError:
            return {"ok": False, "error": "Comando 'patch' no disponible en el sistema. Instalar diffutils."}

        # Actualizar metadata
        meta["status"]     = "applied"
        meta["applied_ts"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        meta["backup"]     = backup_path
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # Registrar en memoria estratégica
        try:
            from core.strategic_memory import record_decision, update_outcome, CAT_EVOLUTION, OUTCOME_SUCCESS
            did = record_decision(
                category=CAT_EVOLUTION,
                title=f"Parche aplicado: {patch_id}",
                description=meta.get("issue", ""),
                action_taken=f"patch aplicado a {target_rel}. Backup en {backup_path}",
            )
            update_outcome(did, OUTCOME_SUCCESS, impact_score=0.5)
        except Exception:
            pass

        with _lock:
            _state["patches_pending"] = _count_pending_patches()

        return {"ok": True, "applied_to": target_rel, "backup": backup_path}

    except Exception as e:
        log.error(f"[SelfReflection] Error aprobando parche {patch_id}: {e}")
        return {"ok": False, "error": str(e)}


def reject_patch(patch_id: str, reason: str = "") -> Dict[str, Any]:
    """Rechaza un parche propuesto."""
    meta_file = os.path.join(PATCHES_DIR, f"{patch_id}_meta.json")
    if not os.path.isfile(meta_file):
        return {"ok": False, "error": f"Parche {patch_id} no encontrado"}
    try:
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)
        meta["status"]        = "rejected"
        meta["rejected_ts"]   = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        meta["reject_reason"] = reason
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        with _lock:
            _state["patches_pending"] = _count_pending_patches()
        return {"ok": True, "patch_id": patch_id}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def rollback_patch(patch_id: str) -> Dict[str, Any]:
    """Revierte un parche aplicado usando el backup .bak guardado."""
    meta_file = os.path.join(PATCHES_DIR, f"{patch_id}_meta.json")
    if not os.path.isfile(meta_file):
        return {"ok": False, "error": f"Parche {patch_id} no encontrado"}
    try:
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)

        if meta.get("status") != "applied":
            return {"ok": False, "error": f"Solo se puede revertir un parche aplicado. Estado actual: {meta.get('status')}"}

        backup = meta.get("backup", "")
        if not os.path.isfile(backup):
            return {"ok": False, "error": f"Backup no encontrado: {backup}"}

        target_rel = ""
        patch_file = meta.get("patch_file", "")
        if os.path.isfile(patch_file):
            with open(patch_file, "r", encoding="utf-8") as f:
                patch_content = f.read()
            m = re.search(r'^--- a/(.+)$', patch_content, re.MULTILINE)
            if m:
                target_rel = m.group(1).strip()

        if target_rel:
            target_abs = os.path.join(BASE_DIR, target_rel)
            with open(backup, "r", encoding="utf-8") as f:
                original = f.read()
            with open(target_abs, "w", encoding="utf-8") as f:
                f.write(original)

        meta["status"]      = "rolled_back"
        meta["rollback_ts"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        return {"ok": True, "restored_file": target_rel or "?"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── Daemon ────────────────────────────────────────────────────────────────────

def _reflection_loop() -> None:
    """Loop daemon del motor de reflexión."""
    log.info(f"[SelfReflection] Daemon iniciado. Ciclo cada {REFLECTION_INTERVAL_H}h.")
    while True:
        try:
            next_run = datetime.now(timezone.utc) + timedelta(hours=REFLECTION_INTERVAL_H)
            with _lock:
                _state["next_run_utc"] = next_run.isoformat().replace("+00:00", "Z")

            run_reflection_cycle()

            wait_secs = REFLECTION_INTERVAL_H * 3600
            time.sleep(wait_secs)
        except Exception as e:
            log.error(f"[SelfReflection] Error en loop: {e}")
            time.sleep(600)  # 10 min de backoff en caso de error


def start() -> None:
    """Inicia el daemon de auto-reflexión si no estaba corriendo."""
    global _started
    if _started:
        return
    _started = True
    t = threading.Thread(target=_reflection_loop, name="GravitySelfReflection", daemon=True)
    t.start()
    log.info("[SelfReflection] Self-Reflection daemon iniciado.")


def get_state() -> Dict[str, Any]:
    """Estado actual del motor de reflexión para el dashboard."""
    with _lock:
        return dict(_state)


def get_last_report() -> Optional[Dict[str, Any]]:
    """Retorna el último informe de introspección."""
    with _lock:
        return _state.get("last_report")
