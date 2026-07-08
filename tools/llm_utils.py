"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   GRAVITY AI — LLM Utils                                                    ║
║                                                                              ║
║   Utilidades compartidas para todos los motores de escritura.               ║
║   Elimina duplicación de clean_response(), atomic_write(), safe_complete()  ║
║   que existían copiadas en book_writer, fiction_writer, book_refiner,       ║
║   y research_writer.                                                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

logger = logging.getLogger("GravityLLMUtils")

# ── Prefijos conversacionales a eliminar ─────────────────────────────────────
_CONVERSATIONAL_PREFIXES = [
    "Aquí tienes el capítulo",
    "Aquí está el capítulo",
    "Claro, aquí",
    "Aquí tienes la continuación",
    "Aquí tienes",
    "Aquí está",
    "A continuación",
    "Entendido.",
    "¡Por supuesto!",
    "Por supuesto,",
]


# ── Limpieza de respuestas LLM ────────────────────────────────────────────────


def clean_response(text: str) -> str:
    """
    Limpia la respuesta de un LLM:
      1. Elimina bloques <think>...</think> (razonamiento interno de modelos como DeepSeek/QwQ).
      2. Elimina bloques de código Markdown residuales (```...).
      3. Elimina prefijos conversacionales genéricos.

    Es seguro usar con texto vacío — retorna "".
    """
    if not text:
        return ""

    # 1. Eliminar bloques <think> cerrados
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    # 2. Si quedó un <think> sin cerrar, corta todo desde ahí
    if "<think>" in cleaned:
        cleaned = re.sub(r"<think>.*", "", cleaned, flags=re.DOTALL).strip()

    # 3. Eliminar bloque de código Markdown al inicio/fin
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9-]*\n", "", cleaned)
        cleaned = re.sub(r"\n```$", "", cleaned)

    # 4. Eliminar prefijos conversacionales
    for prefix in _CONVERSATIONAL_PREFIXES:
        if cleaned.lower().startswith(prefix.lower()):
            lines = cleaned.split("\n")
            while lines and (
                lines[0].lower().startswith(prefix.lower())
                or lines[0].strip() == ""
            ):
                lines.pop(0)
            cleaned = "\n".join(lines).strip()
            break  # Solo aplicar el primer match

    return cleaned


# ── Escritura atómica de archivos ─────────────────────────────────────────────


def atomic_write(filepath: str, content: str) -> None:
    """
    Escribe un archivo de forma atómica usando un .tmp intermedio.
    Previene corrupción en caso de corte de energía o fallo del proceso.
    """
    tmp_path = filepath + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp_path, filepath)


def atomic_append(filepath: str, content: str) -> None:
    """
    Hace un append seguro: lee el archivo, concatena y usa atomic_write.
    """
    existing = ""
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            existing = f.read()
    atomic_write(filepath, existing + content)


# ── Wrapper de llamada al LLM con reintentos ──────────────────────────────────


def safe_complete(
    provider_manager_module: Any,
    messages: list,
    max_retries: int = 3,
    require_json: bool = False,
    retry_delay: float = 2.0,
) -> str:
    """
    Ejecuta provider_manager.complete() con:
      - Reintentos automáticos ante respuestas vacías o muy cortas.
      - Validación de JSON si require_json=True (pide corrección al LLM).
      - clean_response() aplicado a cada respuesta.

    Args:
        provider_manager_module: El módulo core.provider_manager importado por el caller.
        messages: Lista de dicts {role, content}.
        max_retries: Intentos máximos (default 3).
        require_json: Si True, valida que la respuesta sea JSON parseable.
        retry_delay: Segundos entre reintentos.

    Returns:
        Texto limpio, o "" si todos los reintentos fallan.
    """
    current_messages = list(messages)

    for attempt in range(max_retries):
        try:
            response = provider_manager_module.complete(current_messages)
            cleaned = clean_response(response)

            if not cleaned or len(cleaned) < 5:
                logger.warning(
                    f"[safe_complete] Respuesta vacía/corta (intento {attempt+1}/{max_retries}). Reintentando..."
                )
                time.sleep(retry_delay)
                continue

            if require_json:
                try:
                    json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
                    if json_match:
                        json.loads(json_match.group(0))
                    else:
                        json.loads(cleaned)
                except json.JSONDecodeError:
                    logger.warning(
                        f"[safe_complete] JSON inválido (intento {attempt+1}/{max_retries}). "
                        "Pidiendo corrección al LLM..."
                    )
                    current_messages.append({"role": "assistant", "content": response})
                    current_messages.append(
                        {
                            "role": "user",
                            "content": (
                                "Tu respuesta anterior no es un JSON válido. "
                                "Por favor, corrige los errores de sintaxis y devuelve ÚNICAMENTE el JSON válido."
                            ),
                        }
                    )
                    time.sleep(retry_delay)
                    continue

            return cleaned

        except Exception as e:
            logger.error(
                f"[safe_complete] Error en llamada al LLM (intento {attempt+1}/{max_retries}): {e}"
            )
            time.sleep(retry_delay)

    logger.error(f"[safe_complete] Todos los reintentos agotados ({max_retries}).")
    return ""


# ── Compresión de historial acumulado ─────────────────────────────────────────


def compress_history(
    provider_manager_module: Any,
    accumulated_history: str,
    threshold_chars: int = 15000,
) -> str:
    """
    Si el historial supera el umbral de caracteres, lo resume mediante el LLM
    para evitar superar la ventana de contexto en capítulos futuros.

    Args:
        provider_manager_module: El módulo core.provider_manager.
        accumulated_history: Texto del historial acumulado.
        threshold_chars: Umbral en caracteres para activar la compresión (default 15000).

    Returns:
        Historial comprimido, o el original si no supera el umbral.
    """
    if len(accumulated_history) <= threshold_chars:
        return accumulated_history

    logger.info(
        f"[compress_history] Historial de {len(accumulated_history)} chars supera umbral. Comprimiendo..."
    )
    sys_prompt = (
        "Resume el siguiente historial de continuidad de una obra. "
        "Mantén ÚNICAMENTE el estado actual de los personajes/conceptos principales "
        "(vivos, muertos, alianzas, cambios de posición), objetos clave, "
        "y el hilo argumental/argumentativo principal activo. "
        "Hazlo extremadamente denso y omite detalles menores de capítulos viejos.\n\n"
        f"Historial actual:\n{accumulated_history}"
    )
    messages = [{"role": "user", "content": sys_prompt}]
    compressed = safe_complete(provider_manager_module, messages)
    if compressed:
        logger.info(
            f"[compress_history] Comprimido de {len(accumulated_history)} → {len(compressed)} chars."
        )
        return compressed
    # Fallback: si la compresión falla, retornar los últimos threshold_chars
    logger.warning("[compress_history] Compresión falló. Usando truncamiento de emergencia.")
    return accumulated_history[-threshold_chars:]
