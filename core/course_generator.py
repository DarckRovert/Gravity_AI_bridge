"""
Generador Automático de Info-Productos (Cursos / Playlists).
Genera un syllabus y lo inserta en el Scheduler para producción autónoma.
"""

import json
import os
from core.logger import log

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NICHES_PATH = os.path.join(BASE_DIR, "inputs", "niches.json")


def _load_niches() -> dict:
    """Lee niches.json de forma segura."""
    if not os.path.isfile(NICHES_PATH):
        return {"niches": []}
    try:
        with open(NICHES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.error(f"[CourseGenerator] Error leyendo niches.json: {e}")
        return {"niches": []}


def _save_niches(data: dict) -> None:
    """Escribe niches.json de forma segura."""
    os.makedirs(os.path.dirname(NICHES_PATH), exist_ok=True)
    with open(NICHES_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_course(course_title: str, n_videos: int = 10, lang: str = "es") -> bool:
    """
    Genera el syllabus de un curso de N videos e inserta el niche en el scheduler.
    Retorna True si exitoso, False si falla.
    """
    log.info(f"[CourseGenerator] Creando info-producto: '{course_title}' ({n_videos} videos, lang={lang})")

    try:
        from core.provider_manager import get_best, complete

        best_prov, best_model = get_best()
        if best_prov is None or best_model is None:
            log.warning("[CourseGenerator] No hay LLM disponible.")
            return False

        prompt = (
            f"Actúa como un experto creador de Info-productos en YouTube.\n"
            f"Diseña el temario de un curso titulado: '{course_title}' en idioma: {lang}.\n"
            f"El curso tendrá exactamente {n_videos} videos/lecciones.\n"
            "Cada lección debe tener un título muy atractivo y con gancho para YouTube.\n"
            "Responde ÚNICAMENTE con JSON válido, sin explicaciones ni markdown. Formato exacto:\n"
            "{\n"
            '  "course_id": "nombre_corto_sin_espacios_ni_tildes",\n'
            '  "style": "documental",\n'
            '  "bgm_type": "corporativo",\n'
            f'  "topics": ["Lección 1: Título aquí", "Lección 2: Título aquí"]\n'
            "}\n"
        )

        messages = [{"role": "user", "content": prompt}]
        result = complete(
            messages=messages,
            model=best_model,
            provider=best_prov.name,
            options={"temperature": 0.7},
        )

        if not result:
            log.error("[CourseGenerator] LLM devolvió respuesta vacía.")
            return False

        # Parsear JSON con limpieza de markdown
        content = result.strip()
        if content.startswith("```"):
            parts = content.split("```")
            content = parts[1] if len(parts) > 1 else parts[0]
            if content.lower().startswith("json"):
                content = content[4:]
        content = content.strip()

        start = content.find("{")
        end   = content.rfind("}") + 1
        if start == -1 or end <= start:
            log.error(f"[CourseGenerator] No se encontró JSON válido en la respuesta: {content[:200]}")
            return False

        data = json.loads(content[start:end])
        topics = data.get("topics", [])

        if not topics:
            log.error("[CourseGenerator] El LLM no generó ningún topic.")
            return False

        course_id = data.get("course_id", "nuevo_curso").replace(" ", "_")

        # Leer, actualizar y guardar niches.json
        niches_db = _load_niches()
        # Prevenir duplicados por ID
        niches_db["niches"] = [n for n in niches_db.get("niches", []) if n.get("id") != course_id]

        niches_db["niches"].append({
            "id": course_id,
            "topics": topics,
            "style": data.get("style", "documental"),
            "lang": lang,
            "bgm_type": data.get("bgm_type", "corporativo"),
            "n_scenes": 45,
            "estimated_cpm_usd": 15.0,
            "times_used": 0,
            "last_used": None,
        })

        _save_niches(niches_db)
        log.info(f"[CourseGenerator] Curso '{course_title}' ({len(topics)} lecciones) guardado como niche '{course_id}'.")
        return True

    except json.JSONDecodeError as e:
        log.error(f"[CourseGenerator] Error parseando JSON del LLM: {e}")
        return False
    except Exception as e:
        log.error(f"[CourseGenerator] Error inesperado: {e}")
        return False
