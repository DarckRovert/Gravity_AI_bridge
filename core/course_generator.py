"""
Generador Automático de Info-Productos (Cursos / Playlists).
Genera un syllabus utilizando LLMs de forma óptima e inyecta el nuevo nicho en el Scheduler de forma totalmente sincronizada.
"""

import json
from typing import List, Dict, Any
from core.logger import log


def generate_course(course_title: str, n_videos: int = 10, lang: str = "es") -> bool:
    """
    Genera el syllabus estructurado de un curso de N videos e inyecta el nicho de forma sincronizada
    en el planificador autónomo del sistema.

    Args:
        course_title: Título o concepto del info-producto / curso.
        n_videos: Cantidad de lecciones o videos a generar para el temario.
        lang: Idioma de la narración de los contenidos del curso.

    Returns:
        True si el proceso de generación e inyección es exitoso, False en caso contrario.
    """
    log.info(
        f"[CourseGenerator] Creando info-producto: '{course_title}' ({n_videos} videos, lang={lang})"
    )

    try:
        from core.provider_manager import get_best, complete
        from core.content_scheduler import load_niches, save_niches

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
        end = content.rfind("}") + 1
        if start == -1 or end <= start:
            log.error(
                f"[CourseGenerator] No se encontró JSON válido en la respuesta: {content[:200]}"
            )
            return False

        data: Dict[str, Any] = json.loads(content[start:end])
        topics: List[str] = data.get("topics", [])

        if not topics:
            log.error("[CourseGenerator] El LLM no generó ningún topic.")
            return False

        course_id: str = data.get("course_id", "nuevo_curso").replace(" ", "_")

        # Leer, actualizar y guardar niches.json de forma 100% thread-safe mediante delegación
        niches_db = load_niches()

        # Prevenir duplicados por ID
        niches_db["niches"] = [
            n for n in niches_db.get("niches", []) if n.get("id") != course_id
        ]

        niches_db["niches"].append(
            {
                "id": course_id,
                "topics": topics,
                "style": data.get("style", "documental"),
                "lang": lang,
                "bgm_type": data.get("bgm_type", "corporativo"),
                "n_scenes": 45,
                "estimated_cpm_usd": 15.0,
                "times_used": 0,
                "last_used": None,
            }
        )

        save_niches(niches_db)
        log.info(
            f"[CourseGenerator] Curso '{course_title}' ({len(topics)} lecciones) guardado como niche '{course_id}'."
        )
        return True

    except json.JSONDecodeError as e:
        log.error(f"[CourseGenerator] Error parseando JSON del LLM: {e}")
        return False
    except Exception as e:
        log.error(f"[CourseGenerator] Error inesperado: {e}")
        return False
