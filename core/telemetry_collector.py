"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           GRAVITY AI — TELEMETRY COLLECTOR V1.0 [Decoupled Core]             ║
║           Recolector de métricas de hardware, colas, costos y seguridad      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import time
import threading
from typing import Dict, Any, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_FILE = os.path.join(BASE_DIR, "_knowledge.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "_settings.json")

_telemetry_lock = threading.RLock()


def safe_load_json(path: str) -> Dict[str, Any]:
    """Carga JSON con bloqueo reentrante y reintentos ante contención de I/O en Windows."""
    with _telemetry_lock:
        for i in range(5):
            try:
                if not os.path.exists(path):
                    return {}
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (PermissionError, json.JSONDecodeError):
                if i == 4:
                    break
                time.sleep(0.02 * (2**i))
        return {}


def get_provider_status() -> str:
    """Estado de proveedores de IA disponibles."""
    try:
        from core import provider_manager

        scans = provider_manager.scan_all()
        online = [s for s in scans if s.is_healthy]
        best_p, best_m = provider_manager.get_best()
        lines = []
        for s in scans:
            status = "ONLINE" if s.is_healthy else "OFFLINE"
            lat = f"{getattr(s, 'response_ms', 0)}ms" if s.is_healthy else "-"
            lines.append(
                f"  - {s.name}: {status} | {len(s.models)} modelos | latencia {lat}"
            )
        best_str = f"{best_p.name} ({best_m})" if best_p else "Ninguno"
        header = f"PROVEEDORES IA ({len(online)}/{len(scans)} online) | Activo: {best_str}"
        return header + "\n" + "\n".join(lines)
    except Exception as e:
        return f"PROVEEDORES IA: Error consultando estado ({e})"


def get_video_status() -> str:
    """Estado de la cola de generación de video."""
    try:
        from core.video import pipeline

        q = pipeline.get_queue_status()
        pending = q.get("pending", 0)
        processing = q.get("processing", 0)
        done = q.get("done", 0)
        failed = q.get("failed", 0)
        active = q.get("active_job")
        cur_str = f" | Procesando: #{active.get('id', '?')} '{active.get('topic', '')[:30]}'" if active else ""
        return (
            f"COLA DE VIDEO: {pending} pendientes, {processing} en proceso, "
            f"{done} completados, {failed} fallidos{cur_str}"
        )
    except Exception as e:
        return f"COLA DE VIDEO: No disponible ({e})"


def get_image_status() -> str:
    """Estado de la cola de generación de imágenes."""
    try:
        from core import image_queue

        pending = image_queue.get_pending_count()
        return f"COLA DE IMÁGENES: {pending} en cola"
    except Exception as e:
        return f"COLA DE IMÁGENES: No disponible ({e})"


def get_hardware_status() -> str:
    """Métricas de hardware del host."""
    try:
        from core import hardware_profiler

        snap = hardware_profiler.get_profile()
        cpu = snap.get("cpu", {})
        ram = snap.get("ram", {})
        vram = snap.get("vram", {})
        gpu_name = snap.get("gpu", {}).get("name", "GPU")
        return (
            f"HARDWARE: CPU {cpu.get('percent', 0)}% ({cpu.get('cores_logical', 0)} cores) | "
            f"RAM {ram.get('used_gb', 0):.1f}/{ram.get('total_gb', 0):.1f} GB ({ram.get('percent', 0)}%) | "
            f"{gpu_name} VRAM {vram.get('used_gb', 0):.1f}/{vram.get('total_gb', 0):.1f} GB"
        )
    except Exception as e:
        return f"HARDWARE: No disponible ({e})"


def get_cost_status() -> str:
    """Coste de la sesión actual."""
    try:
        from core import cost_tracker

        summary = cost_tracker.get_summary()
        today = summary.get("today_usd", 0.0)
        total = summary.get("total_usd", 0.0)
        calls = summary.get("total_calls", 0)
        limit = summary.get("daily_limit_usd", 5.0)
        pct = (today / limit * 100) if limit > 0 else 0
        return (
            f"COSTES API: Hoy ${today:.4f}/{limit:.2f} ({pct:.0f}%) | "
            f"Total acumulado: ${total:.4f} ({calls} llamadas)"
        )
    except Exception as e:
        return f"COSTES API: No disponible ({e})"


def get_security_status() -> str:
    """Alertas de seguridad activas."""
    try:
        from core import security_monitor

        alerts = security_monitor.get_recent_alerts(limit=3)
        threat = security_monitor.get_threat_level()
        if not alerts:
            return f"SEGURIDAD: Nivel {threat.upper()} | Sin alertas recientes"
        lines = [f"SEGURIDAD: Nivel {threat.upper()} | Últimas alertas:"]
        for a in alerts:
            lines.append(f"  - [{a.get('level', 'INFO')}] {a.get('message', '')[:60]}")
        return "\n".join(lines)
    except Exception as e:
        return f"SEGURIDAD: No disponible ({e})"


def get_audit_status() -> str:
    """Últimas acciones del audit log."""
    try:
        from core import audit_log

        recent = audit_log.get_recent(limit=3)
        if not recent:
            return "AUDIT: Sin acciones registradas en esta sesión"
        lines = ["ÚLTIMAS ACCIONES:"]
        for r in recent:
            lines.append(
                f"  - [{r.get('timestamp', '')[:19]}] {r.get('action', '')}: {r.get('detail', '')[:50]}"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"AUDIT: No disponible ({e})"


def get_image_queue_status() -> str:
    """Estado de la cola de generación de imágenes."""
    try:
        from core import image_queue

        data = image_queue.get_queue_status()
        pending = data.get("pending_count", 0)
        running = data.get("running_count", 0)
        done = data.get("done_count", 0)
        return f"Image Queue: {pending} pendientes | {running} ejecutando | {done} completadas"
    except Exception as e:
        return f"Image Queue: error ({e})"


def get_tiktok_status() -> str:
    """Estado del módulo TikTok Radar (GTLIS)."""
    try:
        from core.tiktok_radar import _load_watchlist
        watchlist = _load_watchlist()
        active = len(watchlist)
        return f"TikTok Radar (GTLIS): {active} objetivos en vigilancia activa."
    except Exception as e:
        return f"TikTok Radar (GTLIS): error ({e})"


def get_autonomy_status() -> str:
    """Estado del motor de autonomía (V16.0 PRO)."""
    try:
        from core.autonomy_engine import get_state as ae_state

        st = ae_state()
        level = st.get("last_status_level", "NORMAL")
        cycles = st.get("cycles_done", 0)
        budget = st.get("budget_remaining_usd", 0)
        actions = st.get("actions_taken", 0)
        pending = st.get("actions_pending_hitl", 0)
        next_cyc = (st.get("next_cycle_utc") or "?")[:19]
        return (
            f"Autonomy Engine: {level} | {cycles} ciclos | "
            f"{actions} acciones ejecutadas | {pending} pendientes HITL | "
            f"Budget restante ${budget:.3f} | Próximo ciclo: {next_cyc}"
        )
    except Exception as e:
        return f"Autonomy Engine: no disponible ({e})"


def get_reflection_status() -> str:
    """Estado del motor de auto-reflexión (V16.0 PRO)."""
    try:
        from core.self_reflection import get_state as refl_state, _count_pending_patches

        st = refl_state()
        issues = st.get("issues_found", 0)
        patches = _count_pending_patches()
        cycles = st.get("cycles_done", 0)
        last_run = (st.get("last_run_utc") or "nunca")[:19]
        return (
            f"Self-Reflection: {cycles} ciclos | {issues} problemas detectados | "
            f"{patches} parche(s) pendiente(s) | Último análisis: {last_run}"
        )
    except Exception as e:
        return f"Self-Reflection: no disponible ({e})"


def get_strategic_memory_snapshot() -> str:
    """Snapshot de la memoria estratégica (V16.0 PRO)."""
    try:
        from core.strategic_memory import get_brain_snapshot

        return get_brain_snapshot()
    except Exception as e:
        return f"Memoria Estratégica: no disponible ({e})"


def get_rag_status() -> str:
    """Estado del índice RAG."""
    try:
        from rag.vector_store import VectorStore
        stats = VectorStore.stats()
        settings = safe_load_json(SETTINGS_FILE)
        enabled = settings.get("rag_enabled", False)
        return f"RAG: {'ACTIVO' if enabled else 'inactivo'} | {stats.get('total_chunks', 0)} chunks en db"
    except Exception as e:
        return f"RAG: error ({e})"


def get_knowledge_status() -> str:
    """Reglas activas del Knowledge Base."""
    try:
        data = safe_load_json(KNOWLEDGE_FILE)
        rules = data.get("persistent_rules", [])
        if not rules:
            return ""
        lines = [f"REGLAS DEL SISTEMA (Knowledge Base — {len(rules)} activas):"]
        for r in rules[-5:]:
            lines.append(f"  • {r}")
        return "\n".join(lines)
    except Exception:
        return ""

