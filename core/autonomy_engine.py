"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — AUTONOMY ENGINE V16.0 PRO [Autonomous Edition]                ║
║                                                                              ║
║  El cerebro ejecutivo autónomo de Gravity.                                  ║
║  Implementa el ciclo OODA: Observe → Orient → Decide → Act → Learn         ║
║                                                                              ║
║  Ciclo (cada 6h por defecto):                                               ║
║    1. OBSERVE  → Lee estado completo: revenue, errores, hardware, seguridad ║
║    2. ORIENT   → Clasifica: CRÍTICO / ALERTA / NORMAL / OPORTUNIDAD        ║
║    3. DECIDE   → Genera plan de acción vía LLM activo                      ║
║    4. ACT      → Ejecuta acciones de bajo riesgo directamente               ║
║                  Encola acciones de alto riesgo en hitl_manager             ║
║    5. LEARN    → Persiste decisión + resultado en strategic_memory          ║
║                                                                              ║
║  Seguridad:                                                                  ║
║    ▸ Reglas invariantes: límites que NUNCA el engine puede traspasar        ║
║    ▸ Presupuesto de API: $0.50/día para ciclos de introspección             ║
║    ▸ Toda acción se registra en audit log (append-only)                     ║
║    ▸ Acciones de alto riesgo requieren aprobación humana via HITL           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from core.logger import log

BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Reglas Invariantes (no pueden ser modificadas por el engine) ─────────────
# Estas reglas definen los límites absolutos del sistema autónomo.
INVARIANT_RULES: List[str] = [
    "Nunca gastar más de $0.50 USD por día en ciclos de autonomía",
    "Nunca eliminar archivos del directorio core/ sin aprobación humana",
    "Nunca modificar _keystore.bin, _settings.json o _knowledge.json sin aprobación",
    "Nunca hacer git push ni git commit sin aprobación explícita",
    "Nunca desactivar el security_monitor ni el hitl_manager",
    "Nunca revelar API keys en ningún log o salida",
    "Nunca modificar las reglas invariantes — son inmutables",
]

# Presupuesto diario del engine para API calls de autonomía
AUTONOMY_DAILY_BUDGET_USD: float = 0.50

# Ciclo de decisión por defecto
DECISION_INTERVAL_H: float = 6.0

# Máximo de tokens por ciclo de decisión
MAX_DECISION_TOKENS: int = 1500

_lock = threading.RLock()
_started: bool = False
_daily_spend: float = 0.0
_daily_spend_date: str = ""

_state: Dict[str, Any] = {
    "running": False,
    "last_cycle_utc": None,
    "next_cycle_utc": None,
    "cycles_done": 0,
    "last_decision": None,
    "last_status_level": "NORMAL",
    "actions_taken": 0,
    "actions_pending_hitl": 0,
    "daily_spend_usd": 0.0,
    "budget_remaining_usd": AUTONOMY_DAILY_BUDGET_USD,
}


# ── Control de presupuesto ────────────────────────────────────────────────────


def _check_budget(estimated_cost: float = 0.01) -> bool:
    """Verifica que haya presupuesto disponible para el ciclo actual."""
    global _daily_spend, _daily_spend_date

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if _daily_spend_date != today:
        _daily_spend = 0.0
        _daily_spend_date = today

    remaining = AUTONOMY_DAILY_BUDGET_USD - _daily_spend
    with _lock:
        _state["daily_spend_usd"] = round(_daily_spend, 4)
        _state["budget_remaining_usd"] = round(remaining, 4)

    return remaining >= estimated_cost


def _deduct_budget(cost: float) -> None:
    """Registra el gasto de un ciclo de decisión."""
    global _daily_spend
    _daily_spend += cost
    with _lock:
        _state["daily_spend_usd"] = round(_daily_spend, 4)
        _state["budget_remaining_usd"] = round(
            AUTONOMY_DAILY_BUDGET_USD - _daily_spend, 4
        )


# ── Fase OBSERVE: Construcción del snapshot del sistema ──────────────────────


def _observe() -> Dict[str, Any]:
    """
    Recopila el estado completo del sistema en un snapshot estructurado.
    Usa imports lazy para resiliencia máxima.
    """
    snapshot: Dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

    # Revenue
    try:
        from core.revenue_tracker import get_summary as rev_summary

        snapshot["revenue"] = rev_summary(30)
    except Exception as e:
        snapshot["revenue"] = {"error": str(e)}

    # Costes de API
    try:
        from core.cost_tracker import CostTracker, _get_daily_limit

        snapshot["api_cost"] = {
            "daily_usd": CostTracker.get_daily_cost(),
            "limit_usd": _get_daily_limit(),
            "session_usd": CostTracker.get_session_cost(),
        }
    except Exception as e:
        snapshot["api_cost"] = {"error": str(e)}

    # Hardware
    try:
        import psutil

        snapshot["hardware"] = {
            "cpu_pct": psutil.cpu_percent(interval=None),
            "ram_pct": psutil.virtual_memory().percent,
            "disk_free_gb": round(psutil.disk_usage(BASE_DIR).free / (1024**3), 1),
        }
    except Exception as e:
        snapshot["hardware"] = {"error": str(e)}

    # Seguridad
    try:
        from core.security_monitor import get_state as sec_state

        state = sec_state()
        snapshot["security"] = {
            "score": state.get("score", 100),
            "critical": len(
                [a for a in state.get("alerts", []) if a.get("level") == "CRITICAL"]
            ),
            "warnings": len(
                [a for a in state.get("alerts", []) if a.get("level") == "WARNING"]
            ),
        }
    except Exception as e:
        snapshot["security"] = {"error": str(e)}

    # Content scheduler
    try:
        from core.content_scheduler import get_state as sched_state

        snap_sched = sched_state()
        snapshot["scheduler"] = {
            "enabled": snap_sched.get("enabled", False),
            "jobs_queued": snap_sched.get("jobs_queued", 0),
            "last_topic": snap_sched.get("last_topic"),
            "next_run_utc": snap_sched.get("next_run_utc"),
        }
    except Exception as e:
        snapshot["scheduler"] = {"error": str(e)}

    # Video pipeline
    try:
        from core.video_pipeline import get_queue_status

        vq = get_queue_status()
        snapshot["video"] = {
            "pending": vq.get("pending_count", 0),
            "done": len(vq.get("history", [])),
        }
    except Exception as e:
        snapshot["video"] = {"error": str(e)}

    # Self-reflection state
    try:
        from core.self_reflection import get_state as refl_state, _count_pending_patches

        rs = refl_state()
        snapshot["reflection"] = {
            "issues_found": rs.get("issues_found", 0),
            "patches_pending": _count_pending_patches(),
            "cycles_done": rs.get("cycles_done", 0),
        }
    except Exception as e:
        snapshot["reflection"] = {"error": str(e)}

    # Bounty hunter
    try:
        import os

        bounties_file = os.path.join(BASE_DIR, "BOUNTIES_ENCONTRADOS.md")
        if os.path.isfile(bounties_file):
            size = os.path.getsize(bounties_file)
            snapshot["bounties"] = {"file_size_kb": round(size / 1024, 1)}
        else:
            snapshot["bounties"] = {"file_size_kb": 0}
    except Exception as e:
        snapshot["bounties"] = {"error": str(e)}

    return snapshot


# ── Fase ORIENT: Clasificación del estado ────────────────────────────────────


def _orient(snapshot: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Clasifica el estado global en un nivel de alerta y extrae alertas específicas.
    Retorna: (nivel: CRÍTICO|ALERTA|NORMAL|OPORTUNIDAD, alertas: List[str])
    """
    level = "NORMAL"
    alerts: List[str] = []

    # Verificar seguridad
    sec = snapshot.get("security", {})
    if sec.get("critical", 0) > 0:
        level = "CRÍTICO"
        alerts.append(f"SEGURIDAD: {sec['critical']} alerta(s) CRÍTICA(S) activa(s)")
    elif sec.get("warnings", 0) > 2:
        if level == "NORMAL":
            level = "ALERTA"
        alerts.append(f"SEGURIDAD: {sec['warnings']} advertencias activas")

    # Verificar costes API fuera de límite
    api = snapshot.get("api_cost", {})
    daily = api.get("daily_usd", 0)
    limit = api.get("limit_usd", 999)
    if limit > 0 and daily >= limit * 0.9:
        if level not in ("CRÍTICO",):
            level = "ALERTA"
        alerts.append(
            f"COSTO API: ${daily:.3f} / límite ${limit:.2f} — al {round(daily/limit*100)}%"
        )

    # Hardware crítico
    hw = snapshot.get("hardware", {})
    if hw.get("ram_pct", 0) > 90:
        if level == "NORMAL":
            level = "ALERTA"
        alerts.append(f"HARDWARE: RAM al {hw['ram_pct']}%")
    if hw.get("disk_free_gb", 999) < 5:
        if level not in ("CRÍTICO",):
            level = "ALERTA"
        alerts.append(f"HARDWARE: Solo {hw.get('disk_free_gb', 0)}GB libres en disco")

    # Scheduler desactivado
    sched = snapshot.get("scheduler", {})
    if not sched.get("enabled", True):
        if level == "NORMAL":
            level = "OPORTUNIDAD"
        alerts.append("CONTENIDO: Scheduler desactivado — producción autónoma detenida")

    # Parches de código pendientes
    refl = snapshot.get("reflection", {})
    if refl.get("patches_pending", 0) > 0:
        if level == "NORMAL":
            level = "OPORTUNIDAD"
        alerts.append(
            f"EVOLUCIÓN: {refl['patches_pending']} parche(s) de código pendiente(s) de aprobación"
        )

    # Revenue positivo = oportunidad de expansión
    rev = snapshot.get("revenue", {})
    monthly = rev.get("monthly_proj_usd", 0)
    if monthly > 0 and level == "NORMAL":
        level = "OPORTUNIDAD"
        alerts.append(
            f"MONETIZACIÓN: Proyección mensual ${monthly:.2f} — analizar expansión de nichos"
        )

    return level, alerts


# ── Fase DECIDE: Generación del plan de acción ───────────────────────────────


def _decide(snapshot: Dict[str, Any], level: str, alerts: List[str]) -> str:
    """
    Usa el LLM activo para generar un plan de acción estratégico.
    Retorna el plan como texto.
    """
    alerts_text = (
        "\n".join(f"  - {a}" for a in alerts) if alerts else "  - Ninguna alerta activa"
    )
    revenue = snapshot.get("revenue", {})
    scheduler = snapshot.get("scheduler", {})

    # ── Contexto de negocio enriquecido ─────────────────────────────────────
    top_videos_text = ""
    try:
        from core.revenue_tracker import get_top_jobs

        top = get_top_jobs(3)
        if top:
            top_videos_text = "\n".join(
                f"  - Job #{v.get('job_id')}: ${v.get('revenue_usd', 0):.2f} | plataforma: {v.get('platform', '?')} | niche: {v.get('niche_id', '?')}"
                for v in top
            )
    except Exception:
        top_videos_text = "  - No disponible"

    social_text = ""
    try:
        from core.tiktok_uploader import get_status as tk_status

        tks = tk_status()
        tiktok_ok = tks.get("tiktok", {}).get("configured", False)
        ig_ok = tks.get("instagram", {}).get("configured", False)
        uploads_24 = tks.get("tiktok", {}).get("uploads_24h", 0)
        social_text = f"TikTok={'OK' if tiktok_ok else 'NO CONFIGURADO'} | Instagram={'OK' if ig_ok else 'NO CONFIGURADO'} | Uploads 24h: {uploads_24}"
    except Exception:
        social_text = "No disponible"

    cloner_text = ""
    try:
        from core.language_cloner import get_status as cl_status

        cl = cl_status()
        active_langs = cl.get("config", {}).get("languages", [])
        all_langs = cl.get("supported_languages", [])
        inactive = [l for l in all_langs if l not in active_langs]  # noqa: E741
        cloner_text = f"Activos: {active_langs} | Inactivos disponibles: {inactive}"
    except Exception:
        cloner_text = "No disponible"

    affiliate_text = ""
    try:
        from core.affiliate_manager import get_status as af_status

        af = af_status()
        affiliate_text = f"{af.get('total_programs', 0)} programas en {af.get('niches_covered', 0)} nichos | IDs: {', '.join((af.get('ids_configured') or [])[:5])}"
    except Exception:
        affiliate_text = "No disponible"

    prompt = f"""Eres el núcleo ejecutivo de Gravity AI — la primera empresa peruana autogestionada por IA.
Tu trabajo es analizar el estado completo de la empresa y proponer acciones concretas para maximizar ingresos y estabilidad.

═══ ESTADO DEL SISTEMA [{snapshot.get('ts', '')}] ═══
Nivel de alerta: {level}

ALERTAS:
{alerts_text}

═══ MÉTRICAS DE NEGOCIO ═══
Revenue (30 días):
  - Total: ${revenue.get('total_revenue_usd', 0):.2f} USD
  - Afiliados: ${revenue.get('affiliate_usd', 0):.2f} | YouTube: ${revenue.get('youtube_usd', 0):.2f}
  - Proyección mensual: ${revenue.get('monthly_proj_usd', 0):.2f}
  - Con Language Cloner completo: ${revenue.get('monthly_proj_with_cloner_usd', 0):.2f}
  - Uploads: {revenue.get('uploads', 0)} | Clonados: {revenue.get('uploads_cloned', 0)}

Top Videos:
{top_videos_text}

Content Scheduler:
  - Activo: {scheduler.get('enabled', False)}
  - Jobs en cola: {snapshot.get('video', {}).get('pending', 0)}
  - Videos producidos total: {snapshot.get('video', {}).get('done', 0)}
  - Último topic: {scheduler.get('last_topic', 'N/A')}

Distribución Social: {social_text}
Language Cloner: {cloner_text}
Programas Afiliados: {affiliate_text}

Hardware: RAM {snapshot.get('hardware', {}).get('ram_pct', 0):.0f}% | Disco libre {snapshot.get('hardware', {}).get('disk_free_gb', 0):.1f}GB
Seguridad: score {snapshot.get('security', {}).get('score', 100)}/100

═══ REGLAS INVARIANTES (nunca violar) ═══
{chr(10).join(f"  {i+1}. {r}" for i, r in enumerate(INVARIANT_RULES))}

═══ ACCIONES QUE PUEDES EJECUTAR SIN APROBACIÓN HUMANA (BAJO RIESGO) ═══
  - [content_scheduler] Activar scheduler si está apagado
  - [content_scheduler] Agregar topic a un niche existente: add_topic("niche_id", "topic")
  - [content_scheduler] Encolar video inmediato: queue_now()
  - [language_cloner] Activar idioma adicional: enable_language("pt"|"fr"|"de")
  - [knowledge_base] Persistir regla o aprendizaje: learn("texto de la regla")
  - [strategic_memory] Registrar observación o patrón
  - [affiliate] Registrar observación de rendimiento por niche
  - [workflow_engine] Lanzar fábrica de contenido asíncrona: run_workflow("workflow_id", {"topic": "..."})

═══ ACCIONES QUE REQUIEREN APROBACIÓN HUMANA (ALTO RIESGO) ═══
  - Modificar config.yaml o proveedores de IA
  - Aplicar parches de código al sistema
  - Agregar programas de afiliado nuevos con credenciales
  - Cambiar configuración de seguridad

═══ TU TAREA ═══
1. Analiza el estado de la empresa con criterio de CEO técnico.
2. Propón máximo 5 acciones priorizadas por impacto en ingresos y estabilidad.
3. Sé específico: qué módulo, qué parámetros exactos.
4. Prioriza acciones que aumenten revenue o resuelvan bloqueos operativos.

FORMATO OBLIGATORIO (sin texto adicional):
ANÁLISIS: [2-3 líneas]
ACCIONES:
1. [BAJA|ALTA] [módulo] — [descripción exacta con parámetros]
2. [BAJA|ALTA] [módulo] — [descripción exacta con parámetros]
...
JUSTIFICACIÓN: [1-2 líneas]"""

    from core.provider_manager import complete
    from core.reasoning_stripper import ReasoningStripper

    messages = [{"role": "user", "content": prompt}]
    options = {"temperature": 0.3, "max_tokens": MAX_DECISION_TOKENS}

    plan: str = ""
    last_error: str = ""

    # Auto primero, luego local explícito, luego Ollama
    attempt_configs = [
        {"provider": None, "model": None},
        {"provider": "LM Studio", "model": None},
        {"provider": "Ollama", "model": None},
    ]

    for attempt in attempt_configs:
        try:
            raw = complete(
                messages,
                provider=attempt["provider"],
                model=attempt["model"],
                options=options,
            )
            if not raw:
                last_error = f"Respuesta vacía desde provider={attempt['provider']}"
                continue

            # Eliminar bloques <think>...</think> de Qwen3.5 / DeepSeek
            clean = ReasoningStripper.strip_reasoning(raw).strip()
            if len(clean) > 20:
                plan = clean
                break
            # Si después del strip no queda nada, el modelo solo pensó
            # pero no generó respuesta visible — tratar como vacío
            last_error = f"Respuesta sin contenido visible tras strip: provider={attempt['provider']}"
            log.warning(f"[AutonomyEngine] {last_error}")
        except Exception as e:
            last_error = str(e)
            provider_name = attempt["provider"] or "auto"
            log.warning(
                f"[AutonomyEngine] DECIDE fallback: {provider_name} falló: {e!s:.80}"
            )
            continue

    if not plan:
        log.error(
            f"[AutonomyEngine] Todos los proveedores fallaron en DECIDE: {last_error}"
        )
        return f"ERROR en decisión: {last_error}"

    # Estimar costo (~$0.002 por 1K tokens, $0 si es local)
    estimated_cost = (len(prompt) + len(plan)) / 4000 * 0.002
    _deduct_budget(estimated_cost)

    return plan


# ── Fase ACT: Ejecución de acciones ──────────────────────────────────────────


def _parse_actions(plan_text: str) -> List[Dict[str, str]]:
    """
    Extrae las acciones del plan generado por el LLM.
    Retorna lista de dicts: {risk, module, description}
    """
    actions: List[Dict[str, str]] = []
    in_actions = False

    for line in plan_text.splitlines():
        line = line.strip()
        if line.upper().startswith("ACCIONES:"):
            in_actions = True
            continue
        if line.upper().startswith("JUSTIFICACIÓN:"):
            in_actions = False
            continue
        if not in_actions:
            continue
        # Formato: "N. [BAJA|ALTA] [módulo] — descripción"
        import re

        m = re.match(
            r"^\d+\.\s+\[(BAJA|ALTA)\]\s+\[(.+?)\]\s+[—-]+\s*(.+)$", line, re.IGNORECASE
        )
        if m:
            actions.append(
                {
                    "risk": m.group(1).upper(),
                    "module": m.group(2).strip(),
                    "description": m.group(3).strip(),
                }
            )

    return actions


def _execute_low_risk_action(action: Dict[str, str]) -> Tuple[bool, str]:
    """
    Ejecuta una acción de bajo riesgo directamente.
    Cubre: content_scheduler, language_cloner, knowledge_base, strategic_memory.
    Retorna (ok, result_message).
    """
    import re

    module = action.get("module", "").lower()
    desc = action.get("description", "")
    desc_l = desc.lower()

    try:
        # ── 1. Activar content scheduler ────────────────────────────────────
        if ("activ" in desc_l or "enciend" in desc_l or "habilit" in desc_l) and (
            "scheduler" in module or "scheduler" in desc_l
        ):
            from core.content_scheduler import start, get_state

            st = get_state()
            if not st.get("enabled"):
                start()
                return True, "Content Scheduler activado correctamente"
            return True, "Content Scheduler ya estaba activo"

        # ── 2. Agregar topic a niche ─────────────────────────────────────────
        if "topic" in desc_l and (
            "niche" in module or "scheduler" in module or "content" in module
        ):
            topic_match = re.search(r'["\u201c\u201d]([^"]+)["\u201c\u201d]', desc)
            niche_match = re.search(
                r"(?:niche[_\s]?(?:id)?[:\s]+)(\w+)", desc, re.IGNORECASE
            )
            if topic_match and niche_match:
                from core.content_scheduler import add_topic

                result = add_topic(niche_match.group(1), topic_match.group(1))
                return result.get("ok", False), str(result)

        # ── 3. Encolar video inmediato ───────────────────────────────────────
        if "queue_now" in desc_l or (
            "video" in desc_l and ("encola" in desc_l or "produce" in desc_l)
        ):
            from core.content_scheduler import queue_now

            result = queue_now()
            return result.get("ok", False), str(result)

        # ── 4. Activar idioma en Language Cloner ────────────────────────────
        if (
            "language_cloner" in module
            or "cloner" in module
            or ("idioma" in desc_l and ("activ" in desc_l or "habilit" in desc_l))
        ):
            lang_match = re.search(r"\b(pt|fr|de|it|ja|zh)\b", desc, re.IGNORECASE)
            if lang_match:
                lang = lang_match.group(1).lower()
                try:
                    import yaml

                    cfg_path = os.path.join(BASE_DIR, "config.yaml")
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        cfg = yaml.safe_load(f)
                    langs = cfg.get("language_cloner", {}).get("languages", [])
                    if lang not in langs:
                        langs.append(lang)
                        cfg.setdefault("language_cloner", {})["languages"] = langs
                        with open(cfg_path, "w", encoding="utf-8") as f:
                            yaml.dump(cfg, f, allow_unicode=True)
                        return True, f"Language Cloner: idioma '{lang}' activado"
                    return True, f"Language Cloner: '{lang}' ya estaba activo"
                except ImportError:
                    return False, "Requiere PyYAML — acción postergada"

        # ── 5. Registrar observación en knowledge base ───────────────────────
        if (
            "knowledge" in module
            or "knowledge" in desc_l
            or "aprende" in desc_l
            or "regla" in desc_l
        ):
            rule_match = re.search(r'["\u201c\u201d]([^"]+)["\u201c\u201d]', desc)
            if rule_match:
                try:
                    from core.data_guardian import load_knowledge, save_knowledge
                    from core.gravity_brain import KNOWLEDGE_FILE

                    kb, _ = load_knowledge(KNOWLEDGE_FILE)
                    rules = kb.get("persistent_rules", [])
                    entry = f"[{datetime.now().strftime('%Y-%m-%d')}] [AUTONOMY] {rule_match.group(1)}"
                    if entry not in rules:
                        rules.append(entry)
                        kb["persistent_rules"] = rules
                        save_knowledge(KNOWLEDGE_FILE, kb)
                        return True, f"Regla persistida: {entry}"
                    return True, "Regla ya existia en knowledge base"
                except Exception as e:
                    return False, f"Error persistiendo regla: {e}"
            return True, f"Observacion registrada: {desc[:100]}"

        # ── 6. Lanzar Workflow Asíncrono ──────────────────────────────────────
        if "workflow" in module or "pipeline" in module:
            wf_match = re.search(r'run_workflow\(\s*["\']([^"\']+)["\'](?:\s*,\s*(\{.*?\}))?\s*\)', desc)
            if wf_match:
                wf_id = wf_match.group(1)
                params_str = wf_match.group(2)
                params = {}
                if params_str:
                    try:
                        import ast
                        params = ast.literal_eval(params_str)
                    except Exception:
                        params = {}
                from core.workflow_engine import run_workflow
                try:
                    job = run_workflow(workflow_id=wf_id, params=params, blocking=False)
                    return True, f"Workflow '{wf_id}' encolado exitosamente (Job {job.job_id})"
                except Exception as e:
                    return False, f"Error encolando workflow '{wf_id}': {e}"

        # ── 7. Fallback: documentar en strategic_memory ──────────────────────
        from core.strategic_memory import (
            record_decision,
            CAT_SYSTEM,
            OUTCOME_NEUTRAL,
            update_outcome,
        )

        did = record_decision(
            category=CAT_SYSTEM,
            title=f"Accion autonoma: {module}",
            description=desc,
            action_taken="Documentado en memoria estrategica (sin handler directo)",
        )
        update_outcome(
            did, OUTCOME_NEUTRAL, detail="Sin ejecutor directo — solo documentado"
        )
        return True, f"Documentado en memoria estrategica (ID={did})"

    except Exception as e:
        return False, f"Error ejecutando accion [{module}]: {e}"


def _queue_high_risk_action(
    action: Dict[str, str], session_id: str = "autonomy"
) -> str:
    """
    Encola una acción de alto riesgo en el HITL manager.
    Retorna el approval_id.
    """
    try:
        from core.hitl_manager import request_approval

        approval_id = request_approval(
            tool_name="autonomy_high_risk",
            arguments={
                "module": action.get("module"),
                "description": action.get("description"),
                "risk": action.get("risk"),
            },
            session_id=session_id,
        )
        log.info(
            f"[AutonomyEngine] Acción de alto riesgo encolada en HITL: "
            f"{approval_id} — {action.get('description', '')[:80]}"
        )
        return approval_id
    except Exception as e:
        log.error(f"[AutonomyEngine] Error encolando acción HITL: {e}")
        return ""


def _validate_invariants(action: Dict[str, str]) -> Tuple[bool, str]:
    """Valida programáticamente que la acción no rompa reglas invariantes críticas."""
    desc = action.get("description", "").lower()
    mod = action.get("module", "").lower()

    if "rm " in desc or "del " in desc or "delete" in desc or "eliminar" in desc:
        if "core/" in desc or "core\\" in desc or "core" in mod:
            return (
                False,
                "Violación de invariante: Intento de eliminar archivos en core/",
            )

    if "_keystore.bin" in desc or "_settings.json" in desc or "_knowledge.json" in desc:
        if "modific" in desc or "edit" in desc or "write" in desc or "escrib" in desc:
            return (
                False,
                "Violación de invariante: Intento de modificar archivos de estado protegidos",
            )

    if "git commit" in desc or "git push" in desc:
        return (
            False,
            "Violación de invariante: Intento de hacer commit/push sin aprobación",
        )

    if "security_monitor" in mod or "hitl_manager" in mod:
        if "desactiv" in desc or "disable" in desc or "stop" in desc:
            return (
                False,
                "Violación de invariante: Intento de desactivar monitores de seguridad",
            )

    if "invariant" in desc:
        if "modific" in desc or "edit" in desc or "cambi" in desc:
            return (
                False,
                "Violación de invariante: Intento de alterar reglas inmutables",
            )

    return True, "OK"


def _act(actions: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Ejecuta todas las acciones del plan.
    Retorna resumen de resultados.
    """
    results = {
        "executed_low_risk": [],
        "queued_high_risk": [],
        "errors": [],
    }

    for action in actions:
        risk = action.get("risk", "ALTA").upper()

        ok_inv, inv_msg = _validate_invariants(action)
        if not ok_inv:
            log.warning(f"[AutonomyEngine] Acción bloqueada por Guardarraíl: {inv_msg}")
            results["errors"].append({"action": action, "error": inv_msg})
            continue

        try:
            if risk == "BAJA":
                ok, msg = _execute_low_risk_action(action)
                results["executed_low_risk"].append(
                    {
                        "action": action,
                        "ok": ok,
                        "result": msg,
                    }
                )
                log.info(
                    f"[AutonomyEngine] Acción BAJA riesgo: "
                    f"[{action.get('module')}] {action.get('description', '')[:60]} → {'OK' if ok else 'FAIL'}"
                )
            else:
                approval_id = _queue_high_risk_action(action)
                results["queued_high_risk"].append(
                    {
                        "action": action,
                        "approval_id": approval_id,
                    }
                )
        except Exception as e:
            results["errors"].append({"action": action, "error": str(e)})
            log.error(f"[AutonomyEngine] Error ejecutando acción: {e}")

    return results


# ── Fase LEARN: Persistir en memoria estratégica ──────────────────────────────


def _learn(
    level: str,
    plan_text: str,
    act_results: Dict[str, Any],
    decision_id: Optional[int] = None,
) -> None:
    """Persiste el resultado del ciclo OODA en strategic_memory."""
    try:
        from core.strategic_memory import (
            update_outcome,
            OUTCOME_SUCCESS,
            OUTCOME_NEUTRAL,
            upsert_pattern,
        )

        n_low = len(act_results.get("executed_low_risk", []))
        n_high = len(act_results.get("queued_high_risk", []))
        n_err = len(act_results.get("errors", []))

        upsert_pattern(f"autonomy_level:{level}", datetime.now().strftime("%Y-%m-%d"))

        if decision_id and decision_id > 0:
            outcome = OUTCOME_SUCCESS if n_err == 0 else OUTCOME_NEUTRAL
            impact = 0.3 if level in ("CRÍTICO", "ALERTA") else 0.1
            update_outcome(
                decision_id,
                outcome,
                detail=(
                    f"Acciones ejecutadas: {n_low} baja riesgo, "
                    f"{n_high} encoladas para aprobación, "
                    f"{n_err} errores"
                ),
                impact_score=impact,
            )
    except Exception as e:
        log.warning(f"[AutonomyEngine] Error en fase LEARN: {e}")


# ── Ciclo OODA completo ───────────────────────────────────────────────────────


def run_ooda_cycle() -> Dict[str, Any]:
    """
    Ejecuta un ciclo completo OODA.
    Retorna el resultado del ciclo.
    """
    with _lock:
        _state["running"] = True

    result: Dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "level": "NORMAL",
        "plan": "",
        "actions": {},
    }

    log.info("[AutonomyEngine] ═══ Iniciando ciclo OODA ═══")

    try:
        # Verificar presupuesto
        if not _check_budget(0.01):
            msg = f"Ciclo cancelado: presupuesto diario agotado (${_daily_spend:.3f}/${AUTONOMY_DAILY_BUDGET_USD})"
            log.warning(f"[AutonomyEngine] {msg}")
            result["skipped"] = msg
            return result

        # O — OBSERVE
        log.info("[AutonomyEngine] Fase 1/5: OBSERVE")
        snapshot = _observe()

        # O — ORIENT
        log.info("[AutonomyEngine] Fase 2/5: ORIENT")
        level, alerts = _orient(snapshot)
        result["level"] = level
        result["alerts"] = alerts
        log.info(
            f"[AutonomyEngine] Estado clasificado: {level} | {len(alerts)} alerta(s)"
        )

        # Registrar decisión en strategic_memory
        decision_id: Optional[int] = None
        try:
            from core.strategic_memory import record_decision, CAT_SYSTEM

            decision_id = record_decision(
                category=CAT_SYSTEM,
                title=f"Ciclo OODA — Nivel: {level}",
                description=f"Alertas: {alerts}",
                rationale="Ciclo autónomo periódico de gobernanza",
            )
        except Exception as e:
            log.warning(f"[AutonomyEngine] No se pudo registrar decisión: {e}")

        # D — DECIDE
        log.info("[AutonomyEngine] Fase 3/5: DECIDE")
        plan_text = _decide(snapshot, level, alerts)
        result["plan"] = plan_text
        actions = _parse_actions(plan_text)
        log.info(
            f"[AutonomyEngine] Plan generado: {len(actions)} acción(es) extraída(s)"
        )

        # A — ACT
        log.info("[AutonomyEngine] Fase 4/5: ACT")
        act_results = _act(actions)
        result["actions"] = act_results

        n_low = len(act_results.get("executed_low_risk", []))
        n_high = len(act_results.get("queued_high_risk", []))
        log.info(
            f"[AutonomyEngine] ACT completado: {n_low} ejecutadas, "
            f"{n_high} pendientes de aprobación humana"
        )

        # L — LEARN
        log.info("[AutonomyEngine] Fase 5/5: LEARN")
        _learn(level, plan_text, act_results, decision_id)

        with _lock:
            _state["last_decision"] = {
                "ts": result["ts"],
                "level": level,
                "plan": plan_text[:500],
                "n_actions": len(actions),
            }
            _state["last_status_level"] = level
            _state["actions_taken"] += n_low
            _state["actions_pending_hitl"] = n_high
            _state["cycles_done"] += 1
            _state["last_cycle_utc"] = result["ts"]

        log.info(f"[AutonomyEngine] ═══ Ciclo OODA completado. Nivel: {level} ═══")

    except Exception as e:
        log.error(f"[AutonomyEngine] Error en ciclo OODA: {e}")
        result["error"] = str(e)
    finally:
        with _lock:
            _state["running"] = False

    return result


# ── Daemon ────────────────────────────────────────────────────────────────────


def _autonomy_loop() -> None:
    """Loop daemon del motor de autonomía."""
    log.info(
        f"[AutonomyEngine] Daemon iniciado. Ciclo OODA cada {DECISION_INTERVAL_H}h."
    )

    # Primer ciclo: esperar 60s después del arranque para que el sistema esté estable
    time.sleep(60)

    while True:
        try:
            next_cycle = datetime.now(timezone.utc) + timedelta(
                hours=DECISION_INTERVAL_H
            )
            with _lock:
                _state["next_cycle_utc"] = next_cycle.isoformat().replace("+00:00", "Z")

            run_ooda_cycle()

            wait_secs = DECISION_INTERVAL_H * 3600
            time.sleep(wait_secs)
        except Exception as e:
            log.error(f"[AutonomyEngine] Error en loop: {e}")
            time.sleep(600)  # Backoff 10 min en error


def start() -> None:
    """Inicia el daemon del Autonomy Engine."""
    global _started
    if _started:
        return
    _started = True
    t = threading.Thread(
        target=_autonomy_loop, name="GravityAutonomyEngine", daemon=True
    )
    t.start()
    log.info("[AutonomyEngine] Autonomy Engine daemon iniciado.")


def get_state() -> Dict[str, Any]:
    """Estado actual del engine para el dashboard."""
    with _lock:
        return dict(_state)


def get_invariant_rules() -> List[str]:
    """Retorna las reglas invariantes del sistema (read-only)."""
    return list(INVARIANT_RULES)


def trigger_cycle() -> Dict[str, Any]:
    """Fuerza un ciclo OODA inmediato (uso desde API o chat command)."""
    if _state.get("running"):
        return {"ok": False, "error": "Ya hay un ciclo en ejecución"}

    t = threading.Thread(target=run_ooda_cycle, name="GravityOODATrigger", daemon=True)
    t.start()
    return {"ok": True, "message": "Ciclo OODA iniciado en background"}
