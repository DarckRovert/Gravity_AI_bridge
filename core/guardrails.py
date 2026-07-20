"""
Gravity AI — Deterministic Pre-LLM Guardrails V1.0 PRO (Mythos Edition)

Filtros de rescate y detección de intenciones críticas mediante expresiones
regulares en microsegundos, previniendo alucinaciones y llamadas innecesarias a LLMs.
"""

import re
from typing import Optional, Dict, Any
from pydantic import BaseModel
from core.logger import log


class GuardrailMatch(BaseModel):
    matched: bool
    action: str  # e.g., "stop", "handoff", "reset", "cancel"
    reason: str
    reply: str


# Regexes optimizados y probados
HANDOFF_REGEX = re.compile(
    r"(hablar|comunicar|contactar)[\s\S]{0,40}?(asesor|humano|persona|alguien)|un asesor|atenci[oó]n humana|agente humano",
    re.IGNORECASE,
)

STOP_REGEX = re.compile(
    r"^(alto|stop|detener|cancelar|cancela todo|parar|emergencia|abortar)$",
    re.IGNORECASE,
)

RESET_REGEX = re.compile(
    r"^(reiniciar|reset|limpiar contexto|borrar memoria|start over)$",
    re.IGNORECASE,
)


def evaluate_pre_llm_guardrails(user_text: str) -> GuardrailMatch:
    """Evalúa la entrada del usuario determinísticamente ANTES de llamar a cualquier LLM."""
    if not user_text:
        return GuardrailMatch(
            matched=False, action="none", reason="", reply=""
        )

    text = user_text.strip()

    # 1. Parada de emergencia
    if STOP_REGEX.search(text):
        log.info(f"[Guardrails] Intent de parada detectado: '{text}'")
        return GuardrailMatch(
            matched=True,
            action="stop",
            reason="stop_command",
            reply="Operación detenida por orden directa del usuario.",
        )

    # 2. Reinicio de memoria / contexto
    if RESET_REGEX.search(text):
        log.info(f"[Guardrails] Intent de reinicio detectado: '{text}'")
        return GuardrailMatch(
            matched=True,
            action="reset",
            reason="reset_command",
            reply="Contexto y memoria reiniciados a su estado base.",
        )

    # 3. Escalado / Handoff a humano
    if HANDOFF_REGEX.search(text):
        log.info(f"[Guardrails] Intent de handoff humano detectado: '{text}'")
        return GuardrailMatch(
            matched=True,
            action="handoff",
            reason="human_requested",
            reply="Entendido. Transfiriendo la sesión a un operador humano...",
        )

    return GuardrailMatch(matched=False, action="none", reason="", reply="")
