import time
from datetime import datetime, timezone
from typing import Dict, Any, List
import json

from core.gravity_brain import (
    APP_VERSION,
    _get_provider_status,
    _get_video_status,
    _get_image_queue_status,
    _get_hardware_status,
    _get_cost_status,
    _get_security_status,
    _get_rag_status,
    _get_recent_audit,
    _get_autonomy_status,
    _get_reflection_status,
    _get_active_plan,
    _get_strategic_memory_snapshot,
    SYSTEM_COMMANDS
)

GRAVITY_SYSTEM_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_system_status",
            "description": "Obtiene el estado completo y en tiempo real del sistema Gravity AI. Incluye métricas de hardware, finanzas, colas de video/imágenes, alertas de seguridad, memoria estratégica y logs recientes. Úsalo SIEMPRE que el usuario te pregunte por tu estado, memoria, contexto o estado del hardware.",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_strategic_memory": {
                        "type": "boolean",
                        "description": "Si es True, incluye el reporte denso de decisiones y memoria estratégica."
                    }
                },
                "required": []
            }
        }
    }
]

def execute_get_system_status(kwargs: Dict[str, Any]) -> str:
    """
    Ejecuta la herramienta de estado y compila el reporte.
    """
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
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
        _get_autonomy_status(),
        "",
        _get_reflection_status(),
    ]

    active_plan = _get_active_plan()
    if active_plan:
        sections.extend(["", "=== PLAN MAESTRO ACTIVO ===", active_plan])

    if kwargs.get("include_strategic_memory", True):
        mem_snapshot = _get_strategic_memory_snapshot()
        if mem_snapshot and "no disponible" not in mem_snapshot:
            sections.extend(["", mem_snapshot])

    sections.extend(["", "=== COMANDOS DEL SISTEMA DISPONIBLES ==="])
    for cmd, desc in SYSTEM_COMMANDS.items():
        sections.append(f"  {cmd} — {desc}")

    return "\n".join(sections)


def handle_tool_call(tool_name: str, kwargs_str: str) -> str:
    try:
        kwargs = json.loads(kwargs_str) if kwargs_str else {}
    except Exception:
        kwargs = {}
        
    if tool_name == "get_system_status":
        return execute_get_system_status(kwargs)
    
    return f"Herramienta {tool_name} desconocida."
