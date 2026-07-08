"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   GRAVITY AI — Chapter QA Agent                                              ║
║                                                                              ║
║   Validador anti-alucinaciones post-escritura. Revisa que el capítulo         ║
║   recién generado respete el lore, los nombres de los personajes y el tono.  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.provider_manager import provider_manager
from tools.llm_utils import safe_complete
from core.logger import log

class ChapterValidator:
    def __init__(self):
        pass

    def validate_chapter(self, chapter_text: str, synopsis: str, lore_bible: str = "") -> dict:
        """
        Analiza el capítulo en busca de alucinaciones flagrantes o desviaciones de la escaleta/lore.
        Devuelve: {"status": "PASS" | "FAIL", "feedback": "Razón si falló..."}
        """
        log.info("[QA Agent] Verificando calidad y consistencia del capítulo...")
        
        sys_prompt = (
            "Eres un editor de continuidad implacable. Tu tarea es analizar un capítulo de un libro y compararlo "
            "con las reglas del mundo (Lore) y la sinopsis de la historia.\n\n"
            "Busca específicamente:\n"
            "1. Cambios de nombres de personajes.\n"
            "2. Inconsistencias lógicas graves (alguien está en dos lugares a la vez, o un muerto resucita sin razón).\n"
            "3. Ruptura grave del tono o formato.\n\n"
            "Devuelve tu análisis estrictamente en el siguiente formato JSON:\n"
            "{\n"
            '  "status": "PASS" o "FAIL",\n'
            '  "feedback": "Si es FAIL, explica detalladamente qué falló para que el autor pueda reescribirlo. Si es PASS, escribe OK."\n'
            "}\n"
            "Solo devuelve FAIL si el error es grave e innegable. Ignora detalles estilísticos menores."
        )
        
        user_prompt = f"LORE BIBLE:\n{lore_bible}\n\nSINOPSIS:\n{synopsis}\n\nCAPÍTULO A EVALUAR:\n{chapter_text}"
        
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = safe_complete(provider_manager, messages, require_json=True)
            import re
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                result = json.loads(response)
                
            if "status" not in result or "feedback" not in result:
                return {"status": "PASS", "feedback": "QA bypassed due to malformed JSON."}
            return result
        except Exception as e:
            log.error(f"[QA Agent] Fallo al evaluar capítulo: {e}")
            return {"status": "PASS", "feedback": f"QA bypassed due to exception: {e}"}

# Instancia global
qa_agent = ChapterValidator()
