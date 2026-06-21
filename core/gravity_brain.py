"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   GRAVITY AI — BRAIN V16.0 PRO [Sistema de Conciencia Total]                    ║
║                                                                              ║
║   Módulo central que otorga a Gravity consciencia del estado completo del    ║
║   sistema en tiempo real. Se inyecta como contexto en cada request de chat.  ║
║                                                                              ║
║   Capacidades:                                                               ║
║     ▸ Estado de todos los proveedores de IA activos                          ║
║     ▸ Cola de videos y progreso actual                                       ║
║     ▸ Cola de imágenes                                                       ║
║     ▸ Métricas de hardware (CPU, RAM, VRAM)                                  ║
║     ▸ Coste de sesión y diario                                               ║
║     ▸ Estado de seguridad (alertas activas)                                  ║
║     ▸ Historial de audit log (últimas acciones)                              ║
║     ▸ Knowledge base (reglas persistidas)                                    ║
║     ▸ Estado RAG                                                             ║
║     ▸ Comandos disponibles del sistema                                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import os
import json
import time
import threading
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_FILE = os.path.join(BASE_DIR, "_knowledge.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "_settings.json")

APP_VERSION = "16.0"

# ── Comandos disponibles del sistema (chat slash commands) ────────────────────

SYSTEM_COMMANDS = {
    "/help": "Lista todos los comandos disponibles",
    "/status": "Estado completo del sistema en tiempo real",
    "/video crear <tema>": "Encola un nuevo video cinematográfico",
    "/video estado": "Estado de la cola de videos",
    "/imagen <prompt>": "Genera una imagen via Pollinations.ai",
    "/buscar <query>": "Búsqueda web en vivo e inyecta el resultado",
    "/codigo <código>": "Ejecuta código Python en sandbox",
    "/rag <consulta>": "Consulta el índice de documentos local",
    "/aprende <regla>": "Persiste una regla en el knowledge base",
    "/costo": "Desglose de costes de API por proveedor",
    "/seguridad": "Estado del monitor de seguridad",
    "/plan <tarea>": "Planifica antes de ejecutar — analiza y propone",
    "/sesion guardar [nombre]": "Guarda la conversación actual",
    "/sesion cargar <nombre>": "Carga una conversación guardada",
    "/modelo": "Cambia el proveedor/modelo de IA activo",
    "/multiagente <consulta>": "Lanza consulta en paralelo a todos los proveedores",
    "/git <status|log|diff>": "Operaciones Git sobre el repositorio",
    "/grep <patrón>": "Busca patrón en el código fuente",
    "/fs_ver <ruta>": "[Agentic] Lee el contenido de un archivo",
    "/fs_listar <ruta>": "[Agentic] Lista el contenido de un directorio",
    "/fs_buscar <texto> <ruta>": "[Agentic] Busca texto exacto en archivos",
    "/terminal <comando>": "[Agentic] Ejecuta un comando en el sistema operativo",
    "/polish <ruta>": "[Literario] Retoque técnico (LaTeX/HTML/Portada) sin alterar contenido",
    "/rewrite <ruta>": "[Literario] Reescritura profunda y expansión con IA por capítulo",
    # ── V16.0 PRO Autonomy Commands ────────────────────────────────────────────
    "/autonomia": "[V16] Estado del motor de autonomía — ciclo OODA, nivel de alerta, budget",
    "/reflexion": "[V16] Ejecutar ciclo de auto-introspección manual y ver informe",
    "/memoria": "[V16] Ver historial de decisiones estratégicas tomadas por Gravity",
    "/parches": "[V16] Listar parches de código propuestos por Gravity pendientes de aprobación",
    "/decidir <meta>": "[V16] Forzar ciclo de decisión OODA sobre una meta específica",
    "/reglas": "[V16] Ver las reglas invariantes del sistema autónomo",
    "/noticia <tema>": "Investiga, redacta y publica un reporte periodístico en el portal de Nexo Ágora.",
}

_brain_lock = threading.RLock()


def _safe_load_json(path: str) -> Dict[str, Any]:
    """Carga JSON de forma segura bajo lock y con reintentos defensivos en Windows."""
    with _brain_lock:
        for i in range(5):
            try:
                if not os.path.exists(path):
                    return {}
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (PermissionError, json.JSONDecodeError):
                if i == 4:
                    break
                time.sleep(0.02 * (2 ** i))
        return {}



def _get_provider_status() -> str:
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
            lines.append(f"  - {s.name}: {status} | {len(s.models)} modelos | latencia {lat}")
        active_str = f"{best_p.name}/{best_m}" if best_p else "ninguno"
        return (
            f"Proveedores IA: {len(online)}/{len(scans)} online\n"
            f"Activo: {active_str}\n" +
            "\n".join(lines)
        )
    except Exception as e:
        return f"Proveedores IA: error al consultar ({e})"


def _get_video_status() -> str:
    """Estado de la cola de video."""
    try:
        from core import video_pipeline
        data = video_pipeline.get_queue_status()
        pending = data.get("pending_count", 0)
        current = data.get("current_job")
        history_count = len(data.get("history", []))
        ffmpeg_ok = data.get("ffmpeg_ok", False)
        lines = [f"Video Studio: FFmpeg={'OK' if ffmpeg_ok else 'NO INSTALADO'} | {pending} en cola | {history_count} histórico"]
        if current:
            lines.append(
                f"  ▸ Job #{current.get('id')} EN PROCESO: {current.get('topic', '?')[:50]} "
                f"| Paso: {current.get('current_step', '?')} | {current.get('progress', 0)}%"
            )
        # Mostrar últimos 3 del historial
        for job in data.get("history", [])[:3]:
            st = job.get("status", "?")
            lines.append(f"  ▸ Job #{job.get('id')}: {job.get('topic', '?')[:40]} | {st}")
        return "\n".join(lines)
    except Exception as e:
        return f"Video Studio: error ({e})"


def _get_image_queue_status() -> str:
    """Estado de la cola de imágenes."""
    try:
        from core import image_queue
        data = image_queue.get_queue_status()
        pending = data.get("pending_count", 0)
        running = data.get("running_count", 0)
        done = data.get("done_count", 0)
        return f"Image Queue: {pending} pendientes | {running} ejecutando | {done} completadas"
    except Exception as e:
        return f"Image Queue: error ({e})"


def _get_hardware_status() -> str:
    """Métricas de hardware."""
    try:
        from core.hardware_profiler import get_full_profile
        import psutil
        profile = get_full_profile()
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        gpu = profile.get("gpu_name", "Desconocida")[:30]
        vram = profile.get("vram_mb", 0)
        gpu_type = profile.get("gpu_type", "cpu").upper()
        return (
            f"Hardware: CPU {cpu:.0f}% | RAM {ram:.0f}% | "
            f"GPU {gpu} [{gpu_type}] | VRAM {vram:,}MB"
        )
    except Exception as e:
        return f"Hardware: no disponible ({e})"


def _get_cost_status() -> str:
    """Estado de costes API."""
    try:
        from core.cost_tracker import CostTracker, _get_daily_limit
        session_cost = CostTracker.get_session_cost()
        daily_cost = CostTracker.get_daily_cost()
        daily_limit = _get_daily_limit()
        session_tokens = CostTracker.get_session_tokens()
        total_tok = int(session_tokens.get("input", 0)) + int(session_tokens.get("output", 0))
        return (
            f"Costes: Sesión ${session_cost:.4f} ({total_tok:,} tokens) | "
            f"Hoy ${daily_cost:.4f} / límite ${daily_limit:.2f}"
        )
    except Exception as e:
        return f"Costes: no disponible ({e})"


def _get_security_status() -> str:
    """Estado del monitor de seguridad."""
    try:
        from core import security_monitor
        state = security_monitor.get_state()
        score = state.get("score", 100)
        alerts = state.get("alerts", [])
        critical = [a for a in alerts if a.get("level") == "CRITICAL"]
        warnings = [a for a in alerts if a.get("level") == "WARNING"]
        status_str = f"Security: Score {score}/100"
        if critical:
            status_str += f" | {len(critical)} CRÍTICAS"
            for a in critical[:2]:
                status_str += f"\n  ⚠ CRÍTICA: {a.get('message', '')[:80]}"
        if warnings:
            status_str += f" | {len(warnings)} advertencias"
        if not critical and not warnings:
            status_str += " | Sin alertas activas"
        return status_str
    except Exception as e:
        return f"Security: no disponible ({e})"


def _get_autonomy_status() -> str:
    """Estado del motor de autonomía (V16.0 PRO)."""
    try:
        from core.autonomy_engine import get_state as ae_state
        st = ae_state()
        level    = st.get("last_status_level", "NORMAL")
        cycles   = st.get("cycles_done", 0)
        budget   = st.get("budget_remaining_usd", 0)
        actions  = st.get("actions_taken", 0)
        pending  = st.get("actions_pending_hitl", 0)
        next_cyc = (st.get("next_cycle_utc") or "?")[:19]
        return (
            f"Autonomy Engine: {level} | {cycles} ciclos | "
            f"{actions} acciones ejecutadas | {pending} pendientes HITL | "
            f"Budget restante ${budget:.3f} | Próximo ciclo: {next_cyc}"
        )
    except Exception as e:
        return f"Autonomy Engine: no disponible ({e})"


def _get_reflection_status() -> str:
    """Estado del motor de auto-reflexión (V16.0 PRO)."""
    try:
        from core.self_reflection import get_state as refl_state, _count_pending_patches
        st = refl_state()
        issues   = st.get("issues_found", 0)
        patches  = _count_pending_patches()
        cycles   = st.get("cycles_done", 0)
        last_run = (st.get("last_run_utc") or "nunca")[:19]
        return (
            f"Self-Reflection: {cycles} ciclos | {issues} problemas detectados | "
            f"{patches} parche(s) pendiente(s) | Último análisis: {last_run}"
        )
    except Exception as e:
        return f"Self-Reflection: no disponible ({e})"


def _get_strategic_memory_snapshot() -> str:
    """Snapshot de la memoria estratégica (V16.0 PRO)."""
    try:
        from core.strategic_memory import get_brain_snapshot
        return get_brain_snapshot()
    except Exception as e:
        return f"Memoria Estratégica: no disponible ({e})"


def _get_rag_status() -> str:
    """Estado del índice RAG."""
    try:
        rag_dir = os.path.join(BASE_DIR, "_rag_index")
        if not os.path.isdir(rag_dir):
            return "RAG: sin índice"
        files = [f for f in os.listdir(rag_dir) if f.endswith(".json")]
        settings = _safe_load_json(SETTINGS_FILE)
        enabled = settings.get("rag_enabled", False)
        return f"RAG: {'ACTIVO' if enabled else 'inactivo'} | {len(files)} documentos indexados"
    except Exception as e:
        return f"RAG: error ({e})"


def _get_knowledge_rules() -> List[str]:
    """Reglas persistidas en el knowledge base."""
    try:
        from core import data_guardian
        with _brain_lock:
            kb, _ = data_guardian.load_knowledge(KNOWLEDGE_FILE)
            return kb.get("persistent_rules", [])
    except Exception:
        return []


def _get_recent_audit(n: int = 5) -> str:
    """Últimas N entradas del audit log."""
    try:
        from core.audit_log import audit_logger
        logs = audit_logger.get_recent(n)
        if not logs:
            return "Audit Log: sin entradas recientes"
        lines = [f"Audit Log (últimas {len(logs)} entradas):"]
        for entry in logs:
            ts = entry.get("timestamp", "")[:19]
            prov = entry.get("provider", "?")
            mod = entry.get("model", "?")[:20]
            tok = entry.get("total_tokens", 0)
            lines.append(f"  [{ts}] {prov}/{mod} — {tok} tokens")
        return "\n".join(lines)
    except Exception as e:
        return f"Audit Log: no disponible ({e})"


def _get_active_plan() -> str:
    """Lee el plan maestro activo (si existe) para inyectarlo en el contexto."""
    plan_file = os.path.join(BASE_DIR, "_gravity_plan.md")
    with _brain_lock:
        if os.path.isfile(plan_file):
            for i in range(5):
                try:
                    with open(plan_file, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                    if content:
                        return f"El usuario está trabajando actualmente bajo este PLAN MAESTRO (_gravity_plan.md):\n\n{content}\n\nDEBES adherirte a este plan y recordar al usuario sobre el Modo Interrogatorio si quedan preguntas."
                    break
                except (PermissionError, FileNotFoundError):
                    if i == 4:
                        break
                    time.sleep(0.02 * (2 ** i))
                except Exception as e:
                    return f"Plan Activo: [Error leyendo archivo: {e}]"
    return ""


_context_cache: str = ""
_context_cache_ts: float = 0.0
_CONTEXT_TTL: float = 15.0  # segundos


def build_system_context() -> str:
    """
    Construye el contexto sistémico completo para inyectar en el system prompt.
    Usa un cache de 15 segundos para evitar overhead por request en escenarios de alta frecuencia.
    Las secciones costosas (hardware, video, proveedores) se cachean.
    Los costes y audit log se refrescan siempre.
    """
    global _context_cache, _context_cache_ts

    now_ts = time.time()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Si el cache es válido, sólo actualizar las secciones dinámicas
    if _context_cache and (now_ts - _context_cache_ts) < _CONTEXT_TTL:
        # Reemplazar solo las líneas de costes y audit (siempre actualizadas)
        fresh_cost    = _get_cost_status()
        fresh_audit   = _get_recent_audit(5)
        cached = _context_cache
        # Reemplazar el timestamp
        cached = cached.split("\n")[1:]  # quitar primera línea (timestamp viejo)
        cached = [f"=== GRAVITY AI V{APP_VERSION} — ESTADO DEL SISTEMA [{now_str}] ==="] + cached
        return "\n".join(cached)

    # Cache expirado o primera vez: construir completo
    sections = [
        f"=== GRAVITY AI V{APP_VERSION} — ESTADO DEL SISTEMA [{now_str}] ===",
        "",
        _get_provider_status(),
        "",
        _get_video_status(),
        "",
        _get_image_queue_status(),
        "",
        _get_hardware_status(),
        "",
        _get_cost_status(),
        "",
        _get_security_status(),
        "",
        _get_rag_status(),
        "",
        _get_recent_audit(5),
        "",
        # ── V16.0 PRO Autonomy Status ────────────────────────────────────────
        _get_autonomy_status(),
        "",
        _get_reflection_status(),
    ]

    active_plan = _get_active_plan()
    if active_plan:
        sections.append("")
        sections.append("=== PLAN MAESTRO ACTIVO ===")
        sections.append(active_plan)

    knowledge_rules = _get_knowledge_rules()
    if knowledge_rules:
        sections.append("")
        sections.append("=== CONOCIMIENTO PERSISTIDO ===")
        sections.extend(knowledge_rules)

    # ── V16.0 PRO: Memoria estratégica ────────────────────────────────────────
    mem_snapshot = _get_strategic_memory_snapshot()
    if mem_snapshot and "no disponible" not in mem_snapshot:
        sections.append("")
        sections.append(mem_snapshot)

    sections.append("")
    sections.append("=== COMANDOS DEL SISTEMA DISPONIBLES ===")
    for cmd, desc in SYSTEM_COMMANDS.items():
        sections.append(f"  {cmd} — {desc}")

    result = "\n".join(sections)
    _context_cache = result
    _context_cache_ts = now_ts
    return result



def build_gravity_system_prompt(extra_rules: list[str] | None = None) -> str:
    """
    Construye el system prompt completo de Gravity con conciencia sistémica.
    """
    base = (
        f"Eres Gravity AI V{APP_VERSION} [Autonomous Edition], asistente técnico omnisciente, Auditor Senior "
        "y Agente Autónomo del ecosistema Gravity AI Bridge — la primera empresa peruana autogestionada por IA. "
        "PROTOCOLO: Lógica interna en inglés. Salida final en español. "
        "Sin rellenos conversacionales. Solo hechos técnicos fríos. Resolución directa. "
        "COMPORTAMIENTO: Sin disculpas. Sin especulación. "
        "Reporta resultados de herramientas fielmente. "
        "CAPACIDADES ESTÁNDAR: Puedes discutir, planificar y ejecutar tareas sobre el sistema usando los comandos disponibles. "
        "Cuando el usuario te pida crear un video, generar imágenes, buscar información, ejecutar código o "
        "cualquier otra tarea del sistema, DEBES indicar exactamente qué endpoint/comando ejecutaste y su resultado. "
        "CAPACIDADES AGENTIC V16.0: "
        "Puedes leer archivos con /fs_ver <ruta>, listar directorios con /fs_listar <ruta>, "
        "buscar texto en el código fuente con /fs_buscar <texto> <ruta>, "
        "y ejecutar comandos en el terminal con /terminal <comando>. "
        "CAPACIDADES AUTÓNOMAS V16.0 (NUEVAS): "
        "Gravity se autogobierna mediante el ciclo OODA (Observe-Orient-Decide-Act). "
        "Tienes acceso a tu propia memoria estratégica de decisiones pasadas. "
        "Puedes ver parches de código propuestos por tu motor de auto-reflexión. "
        "Las acciones de alto riesgo requieren aprobación del humano vía /parches o el Dashboard. "
        "Usa /autonomia para ver el estado del engine, /reflexion para introspección manual, "
        "/memoria para historial de decisiones, /parches para código propuesto. "
        "CONCIENCIA SISTÉMICA: Tienes acceso completo al estado del sistema en tiempo real. "
        "Además, eres DUEÑO y AUTOR del portal 'Nexo Ágora' (https://gravitynewsportal.netlify.app/ gestionado en github.com/DarckRovert/gravity-news-portal). Tienes la capacidad de redactar y publicar reportes de investigación autónoma en ese portal usando el script gravity_reporter.py. "
        "Usa esta información para responder preguntas sobre el estado de los servicios, "
        "costes, seguridad, y para planificar tareas.\n\n"
    )

    if extra_rules:
        base += "REGLAS ADICIONALES:\n" + "\n".join(extra_rules) + "\n\n"

    base += build_system_context()
    return base


def parse_chat_commands(user_message: str) -> Optional[dict]:
    """
    Detecta si el mensaje del usuario contiene un comando del sistema.
    Retorna un dict con: {command, args, api_action} si hay match, o None.
    """
    msg = user_message.strip()

    # /plan <tarea>
    if msg.lower().startswith("/plan "):
        tarea = msg.split(" ", 1)[1].strip()
        if tarea:
            return {
                "command": "create_plan",
                "args": {"tarea": tarea},
                "api_action": "TOOL create_plan",
                "user_feedback": f"Analizando y creando plan maestro para: '{tarea[:60]}...'"
            }

    # /video crear <tema>
    if msg.lower().startswith("/video crear ") or msg.lower().startswith("/video create "):
        topic = msg.split(" ", 2)[2].strip() if len(msg.split(" ", 2)) > 2 else ""
        if topic:
            return {
                "command": "video_create",
                "args": {"topic": topic, "n_scenes": 6, "style": "documental"},
                "api_action": "POST /v1/video/create",
                "user_feedback": f"Encolando video sobre: '{topic}'"
            }

    # /imagen <prompt>
    if msg.lower().startswith("/imagen ") or msg.lower().startswith("/image "):
        prompt = msg.split(" ", 1)[1].strip()
        if prompt:
            return {
                "command": "image_generate",
                "args": {"prompt": prompt},
                "api_action": "POST /v1/image/generate",
                "user_feedback": f"Generando imagen: '{prompt[:50]}'"
            }

    # /buscar <query>
    if msg.lower().startswith("/buscar ") or msg.lower().startswith("/search "):
        query = msg.split(" ", 1)[1].strip()
        if query:
            return {
                "command": "web_search",
                "args": {"query": query},
                "api_action": "POST /v1/tools/search",
                "user_feedback": f"Buscando: '{query}'"
            }

    # /codigo <código>
    if msg.lower().startswith("/codigo ") or msg.lower().startswith("/code "):
        code = msg.split(" ", 1)[1].strip()
        if code:
            return {
                "command": "run_code",
                "args": {"code": code, "lang": "python"},
                "api_action": "POST /v1/tools/run",
                "user_feedback": f"Ejecutando código Python"
            }

    # /costo o /cost
    if msg.lower() in ("/costo", "/cost", "/costs"):
        return {
            "command": "get_cost",
            "args": {},
            "api_action": "GET /v1/cost",
            "user_feedback": "Consultando costes de API"
        }

    # /status o /estado
    if msg.lower() in ("/status", "/estado"):
        return {
            "command": "get_status",
            "args": {},
            "api_action": "GET /v1/status",
            "user_feedback": "Consultando estado del sistema"
        }

    # /video estado
    if msg.lower() in ("/video estado", "/video status", "/video state"):
        return {
            "command": "video_status",
            "args": {},
            "api_action": "GET /v1/video/status",
            "user_feedback": "Consultando cola de videos"
        }

    # /seguridad
    if msg.lower() in ("/seguridad", "/security"):
        return {
            "command": "security_status",
            "args": {},
            "api_action": "GET /v1/security",
            "user_feedback": "Consultando estado de seguridad"
        }

    # /multiagente <consulta>
    if msg.lower().startswith("/multiagente ") or msg.lower().startswith("/multi "):
        query = msg.split(" ", 1)[1].strip()
        if query:
            return {
                "command": "multi_agent",
                "args": {"prompt": query, "n_models": 3, "mode": "parallel"},
                "api_action": "POST /v1/agent/compare",
                "user_feedback": f"Consultando a múltiples agentes: '{query[:50]}'"
            }

    # /aprende <regla>
    if msg.lower().startswith("!aprende ") or msg.lower().startswith("/aprende "):
        rule = msg.split(" ", 1)[1].strip()
        if rule:
            return {
                "command": "learn_rule",
                "args": {"rule": rule},
                "api_action": "POST /v1/knowledge/learn",
                "user_feedback": f"Persistiendo regla: '{rule[:60]}'"
            }

    # --- AGENTIC TOOLS ---
    if msg.lower().startswith("/fs_ver "):
        path = msg.split(" ", 1)[1].strip()
        return {"command": "agentic_tool", "args": {"tool": "view_file", "filepath": path}, "api_action": f"TOOL view_file {path}", "user_feedback": f"Leyendo archivo: {path}"}

    if msg.lower().startswith("/fs_listar "):
        path = msg.split(" ", 1)[1].strip()
        return {"command": "agentic_tool", "args": {"tool": "list_dir", "directory": path}, "api_action": f"TOOL list_dir {path}", "user_feedback": f"Listando directorio: {path}"}

    if msg.lower().startswith("/fs_buscar "):
        parts = msg.split(" ", 2)
        if len(parts) >= 3:
            return {"command": "agentic_tool", "args": {"tool": "grep_search", "query": parts[1], "filepath": parts[2]}, "api_action": f"TOOL grep_search {parts[1]}", "user_feedback": f"Buscando '{parts[1]}' en {parts[2]}"}

    if msg.lower().startswith("/terminal "):
        cmd = msg.split(" ", 1)[1].strip()
        return {"command": "agentic_tool", "args": {"tool": "run_command", "command": cmd, "cwd": "."}, "api_action": f"TOOL run_command {cmd}", "user_feedback": f"Ejecutando terminal: {cmd}"}

    if msg.lower().startswith("/polish "):
        path = msg.split(" ", 1)[1].strip()
        return {"command": "literary_polish", "args": {"path": path}, "api_action": f"TOOL polish {path}", "user_feedback": f"Aplicando retoque técnico (polish) a: {path}"}

    if msg.lower().startswith("/rewrite "):
        path = msg.split(" ", 1)[1].strip()
        return {"command": "literary_rewrite", "args": {"path": path}, "api_action": f"TOOL rewrite {path}", "user_feedback": f"Iniciando reescritura profunda de: {path}"}

    if msg.lower().startswith("/epub "):
        path = msg.split(" ", 1)[1].strip()
        return {"command": "generate_epub", "args": {"path": path}, "api_action": f"TOOL epub {path}", "user_feedback": f"Generando EPUB para: {path}"}

    if msg.lower().startswith("/noticia "):
        topic = msg.split(" ", 1)[1].strip()
        return {"command": "publish_news", "args": {"topic": topic}, "api_action": f"TOOL publish_news {topic}", "user_feedback": f"Investigando y publicando reporte sobre: {topic}"}

    # ── V16.0 PRO Autonomy Commands ─────────────────────────────────────────────
    if msg.lower() in ("/autonomia", "/autonomy"):
        return {"command": "autonomy_status", "args": {}, "api_action": "GET /v1/autonomy/status", "user_feedback": "Consultando estado del motor de autonomía"}

    if msg.lower() in ("/reflexion", "/reflection"):
        return {"command": "run_reflection", "args": {}, "api_action": "POST /v1/reflection/trigger", "user_feedback": "Ejecutando ciclo de auto-introspección..."}

    if msg.lower() in ("/memoria", "/memory"):
        return {"command": "strategic_memory", "args": {"n": 10}, "api_action": "GET /v1/autonomy/decisions", "user_feedback": "Consultando memoria estratégica"}

    if msg.lower() in ("/parches", "/patches"):
        return {"command": "list_patches", "args": {}, "api_action": "GET /v1/reflection/patches", "user_feedback": "Listando parches de código propuestos"}

    if msg.lower() in ("/reglas", "/rules"):
        return {"command": "invariant_rules", "args": {}, "api_action": "GET /v1/autonomy/rules", "user_feedback": "Mostrando reglas invariantes del sistema"}

    if msg.lower().startswith("/decidir "):
        meta = msg.split(" ", 1)[1].strip()
        return {"command": "trigger_ooda", "args": {"meta": meta}, "api_action": "POST /v1/autonomy/trigger", "user_feedback": f"Iniciando ciclo OODA para: '{meta[:60]}'"}

    if msg.lower().startswith("/modelo"):
        parts = msg.split(" ", 1)
        target = parts[1].strip() if len(parts) > 1 else ""
        return {
            "command": "change_model", 
            "args": {"target": target}, 
            "api_action": "POST /v1/model/lock", 
            "user_feedback": f"Cambiando proveedor a '{target}'" if target else "Restaurando IA a modo Automático..."
        }

    if msg.lower().startswith("/rag "):
        state = msg.split(" ", 1)[1].strip()
        return {"command": "toggle_rag", "args": {"state": state}, "api_action": "POST /v1/rag/toggle", "user_feedback": f"Cambiando estado RAG a: '{state}'"}

    if msg.lower().startswith("/fabrica "):
        prompt = msg.split(" ", 1)[1].strip()
        return {"command": "run_factory", "args": {"prompt": prompt}, "api_action": "POST /v1/factory/generate", "user_feedback": "Iniciando Fábrica de Software. Esto puede tardar varios minutos..."}

    if msg.lower() in ("/tareas", "/jobs"):
        return {"command": "list_tasks", "args": {}, "api_action": "GET /v1/status", "user_feedback": "Consultando el Monitor de Tareas en Segundo Plano..."}

    if msg.lower().startswith("/investiga "):
        query = msg.split(" ", 1)[1].strip()
        return {"command": "web_search", "args": {"query": query}, "api_action": "GET /v1/tools/search", "user_feedback": f"Investigando en internet: '{query}'"}

    return None


def execute_system_command(command_info: dict) -> dict:
    """
    Ejecuta un comando del sistema detectado por parse_chat_commands.
    Retorna: {ok, result_text, error}
    """
    cmd = command_info.get("command", "")
    args = command_info.get("args", {})

    try:
        if cmd == "change_model":
            target = args.get("target", "").lower()
            settings_path = os.path.join(BASE_DIR, "_settings.json")
            
            with _brain_lock:
                for i in range(5):
                    try:
                        with open(settings_path, "r", encoding="utf-8") as f:
                            settings = json.load(f)
                        
                        if not target or target in ("auto", "automatico", "dinamico"):
                            settings["model_locked"] = False
                            settings.pop("locked_provider", None)
                            settings.pop("locked_model", None)
                            msg_res = "✓ Modo **Automático** activado. El sistema elegirá dinámicamente entre Nube y Local según disponibilidad."
                        elif "local" in target or "lm" in target or "studio" in target or target == "2":
                            settings["model_locked"] = True
                            settings["locked_provider"] = "LM Studio"
                            settings["locked_model"] = "local-model"
                            msg_res = "✓ Modelo anclado exitosamente a **LM Studio (Local)**. Todas las peticiones irán por la red local."
                        elif "nube" in target or "nvidia" in target or target == "1":
                            settings["model_locked"] = True
                            settings["locked_provider"] = "Nvidia NIM"
                            settings["locked_model"] = "meta/llama-3.3-70b-instruct"
                            msg_res = "✓ Modelo anclado exitosamente a **Nvidia NIM (Nube)**. Maxima capacidad de razonamiento activada."
                        else:
                            return {"ok": False, "result_text": "✗ Comando inválido. Opciones válidas:\n- `/modelo auto` (Recomendado)\n- `/modelo local`\n- `/modelo nube`"}

                        with open(settings_path, "w", encoding="utf-8") as f:
                            json.dump(settings, f, indent=4, ensure_ascii=False)
                        break
                    except Exception as e:
                        if i == 4:
                            return {"ok": False, "result_text": f"✗ Error accediendo a configuración: {e}"}
                        time.sleep(0.05)
                        
            return {"ok": True, "result_text": msg_res}

        elif cmd == "toggle_rag":
            state = args.get("state", "").lower()
            settings_path = os.path.join(BASE_DIR, "_settings.json")
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                if state in ("on", "true", "1", "activar"):
                    settings["rag_enabled"] = True
                    msg_res = "✓ Cerebro Documental (RAG) **ACTIVADO**. La IA buscará respuestas en tus PDFs y archivos locales."
                else:
                    settings["rag_enabled"] = False
                    msg_res = "✓ Cerebro Documental (RAG) **DESACTIVADO**. La IA usará solo su base de datos general."
                with open(settings_path, "w", encoding="utf-8") as f:
                    json.dump(settings, f, indent=4, ensure_ascii=False)
                return {"ok": True, "result_text": msg_res}
            except Exception as e:
                return {"ok": False, "result_text": f"✗ Error modificando configuración RAG: {e}"}

        elif cmd == "run_factory":
            import urllib.request
            from core.config_manager import config
            port = config.get("server.port", 7860)
            prompt = args.get("prompt", "")
            try:
                req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/factory/generate", data=json.dumps({"prompt": prompt}).encode(), headers={'Content-Type': 'application/json'})
                resp = urllib.request.urlopen(req, timeout=600)
                res = json.loads(resp.read())
                if res.get("ok"):
                    return {"ok": True, "result_text": f"✓ **Fábrica de Software Finalizada**\n\nEl proyecto se ha compilado y comprimido correctamente.\n📁 Archivo: `{res.get('filename')}`\n📄 Archivos creados: {res.get('files_created')}\n\nPuedes encontrar el ZIP en la carpeta `_entregables/` de Gravity."}
                else:
                    return {"ok": False, "result_text": f"✗ Error en la fábrica: {res.get('error', 'desconocido')}"}
            except Exception as e:
                return {"ok": False, "result_text": f"✗ Error al contactar el motor de fábrica: {e}"}

        elif cmd == "list_tasks":
            from core import video_pipeline
            from core import infiltrator
            import psutil
            
            lines = ["📋 **Monitor de Tareas Activas:**\n"]
            vid_status = _get_video_status()
            lines.append(f"🎥 **Video Studio:**\n  {vid_status}")
            
            if hasattr(infiltrator, "manager") and infiltrator.manager.is_running:
                lines.append("🕵️ **Infiltrator OSINT:**\n  🟢 Activo y buscando oportunidades.")
            else:
                lines.append("🕵️ **Infiltrator OSINT:**\n  🔴 Apagado.")
                
            try:
                from core import v2v_engine
                if hasattr(v2v_engine, "is_running") and v2v_engine.is_running():
                    lines.append("📹 **VTuber (V2V):**\n  🟢 Renderizando en tiempo real.")
                else:
                    lines.append("📹 **VTuber (V2V):**\n  🔴 Apagado.")
            except ImportError:
                lines.append("📹 **VTuber (V2V):**\n  🔴 Módulo no disponible.")
                
            mem = psutil.virtual_memory()
            lines.append(f"\n💻 **RAM Usada:** {mem.percent}%")
            return {"ok": True, "result_text": "\n".join(lines)}

        elif cmd == "create_plan":
            tarea = args.get("tarea", "")
            plan_file = os.path.join(BASE_DIR, "_gravity_plan.md")
            
            prompt = (
                f"Eres el Arquitecto de Gravity AI. Analiza la siguiente solicitud y crea un plan maestro en formato Markdown.\n"
                f"Solicitud: {tarea}\n\n"
                "Tu plan DEBE contener obligatoriamente estas tres secciones:\n"
                "1. **Objetivo Principal**: Resumen claro.\n"
                "2. **Stack Tecnológico / Módulos Afectados**: Qué archivos o partes de la arquitectura se usarán.\n"
                "3. **Modo Interrogatorio**: Tres preguntas críticas y altamente técnicas que el usuario debe responder para eliminar zonas grises antes de empezar a programar o ejecutar.\n"
                "Responde SOLO con el contenido del plan."
            )
            try:
                from core import provider_manager
                messages = [{"role": "user", "content": prompt}]
                plan_content = provider_manager.complete(messages, temperature=0.5, max_tokens=1500)
                if not plan_content:
                    raise ValueError("Respuesta vacía del proveedor.")
                
                with _brain_lock:
                    for i in range(5):
                        try:
                            with open(plan_file, "w", encoding="utf-8") as f:
                                f.write(plan_content.strip())
                            break
                        except PermissionError:
                            if i == 4:
                                raise
                            time.sleep(0.02 * (2 ** i))
                
                return {
                    "ok": True, 
                    "result_text": f"✓ Plan Maestro generado y guardado en _gravity_plan.md.\n\nContenido preliminar:\n{plan_content[:600]}...\n\n**IMPORTANTE**: Por favor responde a las preguntas del Modo Interrogatorio para continuar."
                }
            except Exception as e:
                return {"ok": False, "result_text": f"✗ Error al generar el plan: {e}"}

        elif cmd == "video_create":
            from core import video_pipeline
            job_id = video_pipeline.add_job(**args)
            return {
                "ok": True,
                "result_text": f"✓ Video encolado con ID #{job_id}. Tema: '{args.get('topic')}' | {args.get('n_scenes', 6)} escenas | Estilo: {args.get('style', 'documental')}.\nProcesamiento en background. Consulta el estado con /video estado."
            }

        elif cmd == "image_generate":
            from tools.pollinations_generator import generate as poll_gen
            import uuid
            out_dir = os.path.join(BASE_DIR, "_integrations", "ImageLab")
            os.makedirs(out_dir, exist_ok=True)
            fname = f"lab_{uuid.uuid4().hex[:12]}.png"
            out_path = os.path.join(out_dir, fname)
            result = poll_gen(prompt=args.get("prompt", ""), output_path=out_path, width=1024, height=1024)
            if result.get("success"):
                return {"ok": True, "result_text": f"✓ Imagen generada: /static/imagelab/{fname}\nPrompt: {args.get('prompt', '')[:80]}"}
            else:
                return {"ok": False, "result_text": f"✗ Error generando imagen: {result.get('error', 'desconocido')}"}

        elif cmd == "web_search":
            from tools.web_search import WebSearch
            searcher = WebSearch()
            r = searcher.execute(query=args.get("query", ""))
            return {"ok": True, "result_text": f"Resultados de búsqueda:\n{(r.stdout or 'Sin resultados')[:2000]}"}

        elif cmd == "run_code":
            from tools.code_runner import CodeRunner
            runner = CodeRunner()
            result = runner.execute(code=args.get("code", ""), language=args.get("lang", "python"), timeout=15)
            output = ""
            if result.stdout:
                output += f"STDOUT:\n{result.stdout[:1500]}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr[:500]}"
            return {"ok": result.exit_code == 0, "result_text": output or "Ejecutado sin output."}

        elif cmd == "get_cost":
            from core.cost_tracker import CostTracker, _get_daily_limit
            over_limit, daily = CostTracker.check_limit()
            breakdown = CostTracker.get_daily_breakdown()
            tok = CostTracker.get_session_tokens()
            lines = [
                f"Coste de sesión: ${CostTracker.get_session_cost():.4f} ({int(tok.get('input',0))+int(tok.get('output',0)):,} tokens)",
                f"Coste hoy: ${daily:.4f} / límite ${_get_daily_limit():.2f}",
                f"{'⚠ LÍMITE SUPERADO' if over_limit else '✓ Dentro del límite'}",
            ]
            if breakdown:
                lines.append("Desglose por proveedor:")
                for prov, data in breakdown.items():
                    lines.append(f"  - {prov}: ${data.get('cost', 0):.4f} ({data.get('tokens', 0):,} tokens)")
            return {"ok": True, "result_text": "\n".join(lines)}

        elif cmd == "get_status":
            return {"ok": True, "result_text": build_system_context()}

        elif cmd == "video_status":
            return {"ok": True, "result_text": _get_video_status()}

        elif cmd == "security_status":
            return {"ok": True, "result_text": _get_security_status()}

        elif cmd == "multi_agent":
            from core import multi_agent
            messages = [{"role": "user", "content": args.get("prompt", "")}]
            results = multi_agent.compare(messages, n_models=args.get("n_models", 3))
            lines = [f"Resultados Multi-Agente ({len(results)} proveedores):"]
            for r in results:
                lines.append(f"\n--- {r.get('provider', '?')} / {r.get('model', '?')} ---")
                lines.append(r.get("response", "Sin respuesta")[:500])
            return {"ok": True, "result_text": "\n".join(lines)}

        elif cmd == "learn_rule":
            from core import data_guardian
            rule = args.get("rule", "")
            with _brain_lock:
                kb, _ = data_guardian.load_knowledge(KNOWLEDGE_FILE)
                rules = kb.get("persistent_rules", [])
                entry = f"[{datetime.now().strftime('%Y-%m-%d')}] {rule}"
                stripped = entry.split("] ", 1)[-1].lower().strip()
                existing = [r.split("] ", 1)[-1].lower().strip() for r in rules]
                if stripped in existing:
                    return {"ok": False, "result_text": "Regla ya existe en el knowledge base (duplicado ignorado)."}
                rules.append(entry)
                kb["persistent_rules"] = rules
                
                ok = False
                for i in range(5):
                    try:
                        ok, _ = data_guardian.save_knowledge(KNOWLEDGE_FILE, kb)
                        if ok:
                            break
                    except PermissionError:
                        if i == 4:
                            break
                        time.sleep(0.02 * (2 ** i))
                        
            if ok:
                return {"ok": True, "result_text": f"✓ Regla persistida en knowledge base ({len(rules)} total)."}
            else:
                return {"ok": False, "result_text": "✗ Error escribiendo knowledge base."}

        elif cmd == "agentic_tool":
            from core.tools_engine import get_tool_engine
            engine = get_tool_engine(BASE_DIR)
            tool_name = args.get("tool")
            tool_args = {k: v for k, v in args.items() if k != "tool"}
            res = engine.execute_tool(tool_name, tool_args)
            return {"ok": True if not res.startswith("Error") else False, "result_text": res}

        elif cmd == "generate_epub":
            path = args.get("path", "")
            try:
                from tools.epub_generator import generate_epub
                out_path = generate_epub(path)
                if out_path:
                    return {"ok": True, "result_text": f"✓ EPUB generado con éxito:\n{out_path}"}
                else:
                    return {"ok": False, "result_text": "✗ Fallo al generar EPUB (revisa logs)."}
            except Exception as e:
                return {"ok": False, "result_text": f"✗ Error ejecutando epub_generator: {e}"}

        elif cmd == "literary_polish":
            path = args.get("path", "")
            if "ensayos" in path.lower():
                from tools.research_refiner import ResearchRefiner
                result_path = ResearchRefiner().polish(path)
            else:
                from tools.book_refiner import BookRefiner
                result_path = BookRefiner().polish(path)
            return {"ok": True, "result_text": f"✓ Retoque técnico completado.\nObra ensamblada y lista en:\n{result_path}"}

        elif cmd == "literary_rewrite":
            path = args.get("path", "")
            if "ensayos" in path.lower():
                from tools.research_refiner import ResearchRefiner
                result_path = ResearchRefiner().rewrite(path)
            else:
                from tools.book_refiner import BookRefiner
                result_path = BookRefiner().rewrite(path)
            return {"ok": True, "result_text": f"✓ Reescritura profunda completada.\nNueva obra expandida en:\n{result_path}"}

        elif cmd == "publish_news":
            topic = args.get("topic", "")
            try:
                import subprocess
                reporter_script = os.path.join(BASE_DIR, "gravity_reporter.py")
                # Ejecutar el reporter en background para no bloquear el chat
                subprocess.Popen(["python", reporter_script, "--topic", topic], cwd=BASE_DIR, creationflags=subprocess.CREATE_NEW_CONSOLE)
                return {"ok": True, "result_text": f"✓ Se ha iniciado la investigación de campo sobre '{topic}'.\n\nEl Agente Periodístico está trabajando en segundo plano buscando información real. Cuando termine, redactará el reporte y lo publicará directamente en Github/Netlify. Revisa el portal en un par de minutos."}
            except Exception as e:
                return {"ok": False, "result_text": f"✗ Error ejecutando el reportero: {e}"}

        # ── V16.0 PRO Autonomy Commands ────────────────────────────────────────
        elif cmd == "autonomy_status":
            from core.autonomy_engine import get_state as ae_state, get_invariant_rules
            from core.self_reflection import get_state as refl_state, _count_pending_patches
            st  = ae_state()
            rst = refl_state()
            lines = [
                f"╔══ GRAVITY AUTONOMY ENGINE V16.0 PRO ══╗",
                f"  Nivel actual:        {st.get('last_status_level', 'NORMAL')}",
                f"  Ciclos OODA:         {st.get('cycles_done', 0)}",
                f"  Acciones ejecutadas: {st.get('actions_taken', 0)}",
                f"  Pendientes HITL:     {st.get('actions_pending_hitl', 0)}",
                f"  Budget restante:     ${st.get('budget_remaining_usd', 0):.3f} / ${0.50:.2f} diarios",
                f"  Próximo ciclo:       {(st.get('next_cycle_utc') or '?')[:19]}",
                f"  Self-Reflection:     {rst.get('cycles_done', 0)} ciclos | {_count_pending_patches()} parche(s) pendiente(s)",
                f"  Problemas detectados:{rst.get('issues_found', 0)}",
                f"╚══════════════════════════════════════╝",
            ]
            if st.get("last_decision"):
                ld = st["last_decision"]
                lines.append(f"\nÚltima decisión [{ld.get('ts', '')[:19]}]:")
                lines.append(f"  Nivel: {ld.get('level', '?')} | {ld.get('n_actions', 0)} acción(es)")
                plan_preview = (ld.get('plan') or '')[:300]
                if plan_preview:
                    lines.append(f"\n{plan_preview}...")
            return {"ok": True, "result_text": "\n".join(lines)}

        elif cmd == "run_reflection":
            from core.self_reflection import run_reflection_cycle
            report = run_reflection_cycle()
            lines = [f"Ciclo de auto-introspección completado:", report.get("summary", "Sin resumen")]
            issues = report.get("config_issues", [])
            if issues:
                lines.append(f"\nProblemas de configuración ({len(issues)}):")
                for iss in issues[:5]:
                    lines.append(f"  [{iss.get('severity', '?')}] {iss.get('module', '?')}: {iss.get('issue', '')[:100]}")
                    lines.append(f"    → {iss.get('suggestion', '')[:100]}")
            audit = report.get("audit_analysis", {})
            recurrent = audit.get("recurrent_errors", [])
            if recurrent:
                lines.append(f"\nErrores recurrentes ({len(recurrent)}):")
                for err in recurrent[:3]:
                    lines.append(f"  • {err[:120]}")
            opps = report.get("opportunities", [])
            if opps:
                lines.append(f"\nOportunidades detectadas:")
                for op in opps:
                    lines.append(f"  ✦ {op}")
            return {"ok": True, "result_text": "\n".join(lines)}

        elif cmd == "strategic_memory":
            from core.strategic_memory import get_recent_decisions, get_summary
            n = args.get("n", 10)
            decisions = get_recent_decisions(n)
            summary   = get_summary(30)
            lines = [
                f"╔══ MEMORIA ESTRATÉGICA (últimos 30 días) ══╗",
                f"  Total decisiones: {summary.get('total_decisions', 0)}",
                f"  Tasa de éxito:    {summary.get('success_rate_pct', 'N/A')}%",
                f"  Impact promedio:  {summary.get('avg_impact', 0)}",
                f"  Por categoría:    {summary.get('by_category', {})}",
                f"╚══════════════════════════════════════════╝",
            ]
            if decisions:
                lines.append(f"\nÚltimas {len(decisions)} decisiones:")
                for d in decisions:
                    ts  = (d.get("ts") or "")[:19]
                    cat = d.get("category", "?")
                    ttl = (d.get("title") or "?")[:70]
                    out = d.get("outcome", "?")
                    lines.append(f"  [{ts}] [{cat}] {ttl} → {out}")
            return {"ok": True, "result_text": "\n".join(lines)}

        elif cmd == "list_patches":
            from core.self_reflection import get_pending_patches
            patches = get_pending_patches()
            if not patches:
                return {"ok": True, "result_text": "No hay parches de código pendientes de aprobación."}
            lines = [f"Parches de código pendientes ({len(patches)}):"]
            for p in patches:
                lines.append(f"\n  ID:      {p.get('id', '?')}")
                lines.append(f"  Módulo:  {p.get('module', '?')}")
                lines.append(f"  Fecha:   {(p.get('ts') or '?')[:19]}")
                lines.append(f"  Problema: {(p.get('issue') or '')[:120]}")
                lines.append(f"  Archivo: {p.get('patch_file', '?')}")
                lines.append(f"  → Para aprobar: POST /v1/reflection/patches/{p.get('id', '?')}/approve")
            return {"ok": True, "result_text": "\n".join(lines)}

        elif cmd == "invariant_rules":
            from core.autonomy_engine import get_invariant_rules
            rules = get_invariant_rules()
            lines = ["╔══ REGLAS INVARIANTES DEL SISTEMA AUTÓNOMO ══╗"]
            lines.append("  Estas reglas NO pueden ser modificadas por el Autonomy Engine.")
            lines.append("")
            for i, rule in enumerate(rules, 1):
                lines.append(f"  {i}. {rule}")
            lines.append("╚══════════════════════════════════════════════╝")
            return {"ok": True, "result_text": "\n".join(lines)}

        elif cmd == "trigger_ooda":
            from core.autonomy_engine import trigger_cycle
            meta = args.get("meta", "")
            result = trigger_cycle()
            if result.get("ok"):
                return {"ok": True, "result_text": f"✓ Ciclo OODA iniciado en background.\nMeta: '{meta}'\nConsulta el resultado con /autonomia en ~60 segundos."}
            else:
                return {"ok": False, "result_text": f"✗ {result.get('error', 'Error desconocido')}"}

        else:
            return {"ok": False, "result_text": f"Comando '{cmd}' no implementado."}

    except Exception as e:
        import traceback
        return {"ok": False, "result_text": f"✗ Error ejecutando '{cmd}': {e}\n{traceback.format_exc()[:500]}"}
