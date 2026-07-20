"""
Gravity AI — LLM Frontier V1.0 PRO (Mythos Edition)

Frontera única de interacción LLM con validación Pydantic estricta,
extracción robusta de JSON y auto-corrección mediante reintentos.
"""

import json
import time
import re
from typing import TypeVar, Generic, Type, Optional, List, Dict, Any, Union
from pydantic import BaseModel, ValidationError
from core.logger import log

T = TypeVar("T", bound=BaseModel)


class ChatResult(BaseModel, Generic[T]):
    ok: bool
    data: Optional[Any] = None  # Instancia de T si ok=True
    raw: str = ""
    error: Optional[str] = None
    detail: Optional[str] = None
    attempts: int = 1


def _extract_json_str(text: str) -> Optional[str]:
    """Extracción robusta de JSON en 3 etapas:
    1. Bloque de código ```json ... ```
    2. Texto completo si es un JSON directo
    3. Primer substring de {...} o [...] balanceado
    """
    if not text:
        return None

    # Etapa 1: Markdown code block
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Etapa 2: Direct JSON strip
    stripped = text.strip()
    if (stripped.startswith("{") and stripped.endswith("}")) or (
        stripped.startswith("[") and stripped.endswith("]")
    ):
        return stripped

    # Etapa 3: Primer bloque { ... } balanceado
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        return text[first_brace : last_brace + 1]

    first_bracket = text.find("[")
    last_bracket = text.rfind("]")
    if first_bracket != -1 and last_bracket > first_bracket:
        return text[first_bracket : last_bracket + 1]

    return None


def chat_structured(
    schema: Type[T],
    complete_fn: Any,  # función (messages: List[Dict], **kwargs) -> str
    messages: List[Dict[str, Any]],
    max_attempts: int = 3,
    retry_delay_ms: int = 500,
    **completion_kwargs: Any,
) -> ChatResult[T]:
    """Ejecuta una llamada a LLM garantizando salida validada contra un esquema Pydantic.

    Si la salida falla en formato o esquema, reintenta hasta max_attempts veces
    inyectando mensajes de corrección estrictos.
    """
    current_messages = [m.copy() for m in messages]

    # Inyectar instrucción de salida en el system prompt o como nuevo mensaje
    schema_json = json.dumps(schema.model_json_schema(), indent=2)
    format_instruction = (
        f"\n\n[INSTRUCCIÓN DE FORMATO STRICTO]\n"
        f"Debes responder ÚNICAMENTE con un JSON válido que cumpla estrictamente "
        f"con el siguiente esquema Pydantic (JSON Schema):\n"
        f"```json\n{schema_json}\n```\n"
        f"No incluyas explicaciones, preámbulos ni marcas fuera del objeto JSON."
    )

    # Inyectar en el primer mensaje de sistema o crear uno
    if current_messages and current_messages[0].get("role") == "system":
        current_messages[0]["content"] += format_instruction
    else:
        current_messages.insert(
            0, {"role": "system", "content": f"Eres un asistente de IA preciso.{format_instruction}"}
        )

    last_raw = ""
    last_error = ""

    for attempt in range(1, max_attempts + 1):
        try:
            if attempt > 1:
                # Inyectar feedback de corrección en reintentos
                correction_msg = (
                    f"STRICT CORRECTION (Intento {attempt}/{max_attempts}): "
                    f"Tu respuesta previa no pudo ser validada. Error: {last_error}. "
                    f"Corrige tu respuesta y devuelve ÚNICAMENTE el objeto JSON requerido."
                )
                current_messages.append({"role": "system", "content": correction_msg})
                time.sleep((retry_delay_ms * (attempt - 1)) / 1000.0)

            # Invocación al proveedor LLM
            raw_response = complete_fn(current_messages, **completion_kwargs)
            if not isinstance(raw_response, str):
                raw_response = str(raw_response or "")
            last_raw = raw_response

            # Extracción de JSON
            extracted_json = _extract_json_str(raw_response)
            if not extracted_json:
                last_error = "no_json_found (No se detectó estructura JSON válida en el texto)"
                log.warning(
                    f"[LLMFrontier] Intento {attempt}/{max_attempts} falló: {last_error}"
                )
                continue

            # Parseo JSON
            parsed_dict = json.loads(extracted_json)

            # Validación Pydantic
            validated_data = schema.model_validate(parsed_dict)

            log.info(
                f"[LLMFrontier] Éxito al parsear y validar {schema.__name__} en intento {attempt}"
            )
            return ChatResult(
                ok=True,
                data=validated_data,
                raw=last_raw,
                attempts=attempt,
            )

        except json.JSONDecodeError as e:
            last_error = f"json_decode_error ({str(e)})"
            log.warning(
                f"[LLMFrontier] Intento {attempt}/{max_attempts} JSONDecodeError: {e}"
            )
        except ValidationError as e:
            last_error = f"pydantic_validation_error ({e.errors()})"
            log.warning(
                f"[LLMFrontier] Intento {attempt}/{max_attempts} ValidationError: {e}"
            )
        except Exception as e:
            last_error = f"provider_execution_error ({str(e)})"
            log.error(
                f"[LLMFrontier] Error no esperado en intento {attempt}: {e}"
            )

    # Si se agotan los reintentos
    log.error(
        f"[LLMFrontier] Se agotaron los {max_attempts} intentos para validar {schema.__name__}"
    )
    return ChatResult(
        ok=False,
        raw=last_raw,
        error="validation_failed_after_retries",
        detail=last_error,
        attempts=max_attempts,
    )
