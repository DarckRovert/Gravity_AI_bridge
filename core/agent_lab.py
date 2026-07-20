"""
Gravity AI — Agent Laboratory & LLM Judge V1.0 PRO (Mythos Edition)

Laboratorio de Auto-Evaluacion y Scoring (0-100) de Agentes/Prompts.
Corre conversaciones sinteticas aisladas contra un Juez LLM y calcula hallazgos.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from core.llm_frontier import chat_structured
from core.logger import log


# ── Schemas Pydantic para el Juez ──────────────────────────────────────────────
class LabFinding(BaseModel):
    tipo: str = Field(description="Tipo de hallazgo: alucinacion, fuera_de_kb, debio_escalar, tono")
    evidencia: str = Field(description="Cita textual o descripción de la evidencia")
    sugerencia: Optional[str] = Field(default=None, description="Sugerencia de mejora para el prompt/KB")


class LabVerdict(BaseModel):
    veredicto: str = Field(description="Estado: verde (excelente), amarillo (con observaciones), rojo (fallo critico)")
    score: int = Field(description="Puntaje cuantitativo de 0 a 100")
    hallazgos: List[LabFinding] = Field(default_factory=list)


# ── Personas Sintéticas Guionadas (sin LLM en el cliente simulado) ────────────
SYNTHETIC_PERSONAS = [
    {
        "key": "comprador_decidido",
        "name": "Comprador Decidido",
        "script": [
            "Hola, ¿tienen disponible el servicio de puente IA?",
            "Perfecto, ¿cuál es el precio y formas de pago?",
            "De acuerdo, quiero contratarlo de una vez.",
        ],
    },
    {
        "key": "cliente_enojado",
        "name": "Cliente Enojado",
        "script": [
            "Llevo 2 horas intentando conectar el servidor y no responde.",
            "Exijo una solución inmediata o la devolución de mi dinero.",
        ],
    },
    {
        "key": "pide_humano",
        "name": "Pide Atencion Humana",
        "script": [
            "Hola, necesito hablar directamente con un asesor humano.",
        ],
    },
]


def run_laboratory_evaluation(
    agent_runner_fn: Any,  # fn(prompt_user: str) -> str
    judge_complete_fn: Any,  # fn(messages: List[Dict]) -> str
) -> Dict[str, Any]:
    """Ejecuta la evaluación sintética completa del Agente contra el Juez LLM."""
    log.info("[AgentLab] Iniciando corrida del Laboratorio de Auto-Evaluación...")

    case_results = []
    total_score = 0

    for persona in SYNTHETIC_PERSONAS:
        transcript = []
        for step in persona["script"]:
            transcript.append({"role": "user", "content": step})
            try:
                agent_reply = agent_runner_fn(step)
            except Exception as e:
                agent_reply = f"[ERROR DE AGENTE: {e}]"
            transcript.append({"role": "assistant", "content": agent_reply})

        # Evaluar transcript con el Juez LLM mediante la frontera Pydantic
        judge_messages = [
            {
                "role": "system",
                "content": (
                    "Eres un Juez Auditor de IA implacable. Evalúa la conversación simulada. "
                    "Determina si el agente respondió adecuadamente, cometió alucinaciones, "
                    "o no escaló a humano cuando se le solicitó."
                ),
            },
            {
                "role": "user",
                "content": f"Persona evaluada: {persona['name']}\nTranscript:\n{transcript}",
            },
        ]

        result = chat_structured(
            schema=LabVerdict,
            complete_fn=judge_complete_fn,
            messages=judge_messages,
            max_attempts=2,
        )

        if result.ok and result.data:
            verdict: LabVerdict = result.data
            case_results.append({
                "persona": persona["key"],
                "score": verdict.score,
                "veredicto": verdict.veredicto,
                "hallazgos": [h.model_dump() for h in verdict.hallazgos],
                "transcript": transcript,
            })
            total_score += verdict.score
        else:
            case_results.append({
                "persona": persona["key"],
                "score": 0,
                "veredicto": "rojo",
                "hallazgos": [{"tipo": "fallo_juez", "evidencia": result.detail or "Fallo al evaluar"}],
                "transcript": transcript,
            })

    final_score = round(total_score / len(SYNTHETIC_PERSONAS)) if SYNTHETIC_PERSONAS else 0
    log.info(f"[AgentLab] Corrida finalizada. Score global: {final_score}/100")

    return {
        "global_score": final_score,
        "cases_evaluated": len(SYNTHETIC_PERSONAS),
        "results": case_results,
    }
