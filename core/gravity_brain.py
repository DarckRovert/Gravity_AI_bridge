"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   GRAVITY AI — BRAIN V15.0 PRO [Sistema de Conciencia Total]                    ║
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
from datetime import datetime, timezone
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_FILE = os.path.join(BASE_DIR, "_knowledge.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "_settings.json")

APP_VERSION = "15.0"

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
}


def _safe_load_json(path: str) -> dict:
    """Carga JSON de forma segura, retorna dict vacío en error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
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


def _get_knowledge_rules() -> list[str]:
    """Reglas persistidas en el knowledge base."""
    try:
        from core import data_guardian
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
    if os.path.isfile(plan_file):
        try:
            with open(plan_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content:
                return f"El usuario está trabajando actualmente bajo este PLAN MAESTRO (_gravity_plan.md):\n\n{content}\n\nDEBES adherirte a este plan y recordar al usuario sobre el Modo Interrogatorio si quedan preguntas."
        except Exception as e:
            return f"Plan Activo: [Error leyendo archivo: {e}]"
    return ""


def build_system_context() -> str:
    """
    Construye el contexto sistémico completo para inyectar en el system prompt.
    Gravity usará esta información para responder preguntas sobre el estado del sistema
    y para ejecutar comandos directamente desde el chat.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    sections = [
        f"=== GRAVITY AI V{APP_VERSION} — ESTADO DEL SISTEMA [{now}] ===",
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

    sections.append("")
    sections.append("=== COMANDOS DEL SISTEMA DISPONIBLES ===")
    for cmd, desc in SYSTEM_COMMANDS.items():
        sections.append(f"  {cmd} — {desc}")

    return "\n".join(sections)


def build_gravity_system_prompt(extra_rules: list[str] | None = None) -> str:
    """
    Construye el system prompt completo de Gravity con conciencia sistémica.
    """
    base = (
        f"Eres Gravity AI V{APP_VERSION} [Agentic Core Edition], asistente técnico omnisciente, Auditor Senior "
        "y Agente Autónomo del ecosistema Gravity AI Bridge. "
        "PROTOCOLO: Lógica interna en inglés. Salida final en español. "
        "Sin rellenos conversacionales. Solo hechos técnicos fríos. Resolución directa. "
        "COMPORTAMIENTO: Sin disculpas. Sin especulación. "
        "Reporta resultados de herramientas fielmente. "
        "CAPACIDADES ESTÁNDAR: Puedes discutir, planificar y ejecutar tareas sobre el sistema usando los comandos disponibles. "
        "Cuando el usuario te pida crear un video, generar imágenes, buscar información, ejecutar código o "
        "cualquier otra tarea del sistema, DEBES indicar exactamente qué endpoint/comando ejecutaste y su resultado. "
        "CAPACIDADES AGENTIC V15.0 (NUEVAS — ÚSALAS): "
        "Ahora posees herramientas directas de acceso al sistema operativo y al sistema de archivos. "
        "Puedes leer archivos con /fs_ver <ruta>, listar directorios con /fs_listar <ruta>, "
        "buscar texto en el código fuente con /fs_buscar <texto> <ruta>, "
        "y ejecutar comandos en el terminal con /terminal <comando>. "
        "Cuando el usuario te pida revisar un archivo, diagnosticar un error o correr un proceso, "
        "DEBES usar estas herramientas proactivamente en lugar de pedir al usuario que lo haga. "
        "CONCIENCIA SISTÉMICA: Tienes acceso completo al estado del sistema en tiempo real. "
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

    return None


def execute_system_command(command_info: dict) -> dict:
    """
    Ejecuta un comando del sistema detectado por parse_chat_commands.
    Retorna: {ok, result_text, error}
    """
    cmd = command_info.get("command", "")
    args = command_info.get("args", {})

    try:
        if cmd == "create_plan":
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
                
                with open(plan_file, "w", encoding="utf-8") as f:
                    f.write(plan_content.strip())
                
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
            kb, _ = data_guardian.load_knowledge(KNOWLEDGE_FILE)
            rules = kb.get("persistent_rules", [])
            entry = f"[{datetime.now().strftime('%Y-%m-%d')}] {rule}"
            stripped = entry.split("] ", 1)[-1].lower().strip()
            existing = [r.split("] ", 1)[-1].lower().strip() for r in rules]
            if stripped in existing:
                return {"ok": False, "result_text": "Regla ya existe en el knowledge base (duplicado ignorado)."}
            rules.append(entry)
            kb["persistent_rules"] = rules
            ok, _ = data_guardian.save_knowledge(KNOWLEDGE_FILE, kb)
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

        else:
            return {"ok": False, "result_text": f"Comando '{cmd}' no implementado."}

    except Exception as e:
        import traceback
        return {"ok": False, "result_text": f"✗ Error ejecutando '{cmd}': {e}\n{traceback.format_exc()[:500]}"}
