import re
from typing import Dict, Any
from core.hook_engine import BaseHook, hook_manager
from core.logger import log

class QualityAuditorHook(BaseHook):
    NAME = "LLMQualityAuditor"
    TARGET_NODES = ["LLMQuery"]

    # Clichés clásicos de los LLMs que rompen la inmersión del periodista
    AI_CLICHES = [
        r"es importante destacar",
        r"en conclusi[óo]n",
        r"es fascinante",
        r"cabe se[ñn]alar",
        r"ad[ée]ntrate en",
        r"en resumen",
        r"es fundamental mencionar",
        r"sum[ée]rgete en"
    ]

    def post_execute(self, node_id: str, node_type: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Limpia el resultado de un LLMQuery.
        Asume que LLMQuery retorna un diccionario con la llave 'text' o 'result'.
        """
        # Extraemos el texto si existe
        text_key = None
        if "text" in result:
            text_key = "text"
        elif "result" in result:
            text_key = "result"
        elif "content" in result:
            text_key = "content"

        if not text_key:
            return result

        original_text = result[text_key]
        if not isinstance(original_text, str):
            return result

        cleaned_text = original_text

        # 1. Remover Emojis (Gravity AI es cínico, no usa emojis en sus reportes largos)
        # 1. (Remoción de Emojis omitida por falta de dependencia)
        # 2. Remover clichés de IA
        cliches_found = 0
        for cliche in self.AI_CLICHES:
            # Reemplazar ignorando mayúsculas/minúsculas
            pattern = re.compile(cliche + r"[:,.]?\s*", re.IGNORECASE)
            # Contamos cuántos encontró antes de sustituir para el log
            matches = pattern.findall(cleaned_text)
            if matches:
                cliches_found += len(matches)
                cleaned_text = pattern.sub("", cleaned_text)

        if cleaned_text != original_text:
            log.info(f"[{self.NAME}] Se censuraron emojis o clichés ({cliches_found} cliches) en el nodo {node_id}")
            result[text_key] = cleaned_text

        return result

# Auto-registro
hook_manager.register(QualityAuditorHook())
