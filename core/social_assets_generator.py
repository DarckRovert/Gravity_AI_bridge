"""
Generador automático de activos sociales (Twitter/X, Instagram, LinkedIn).
Se ejecuta automáticamente al finalizar cada video.
"""

import json
import os
from core.logger import log

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def generate_social_assets(job_id: int, script_path: str, output_path: str, lang: str = "es") -> bool:
    """
    Lee el guion JSON y genera activos de marketing para redes sociales.
    Retorna True si se completó, False si falló (nunca lanza excepciones).
    """
    if not os.path.isfile(script_path):
        log.warning(f"[SocialAssets] Job #{job_id}: script.json no encontrado en {script_path}")
        return False

    try:
        with open(script_path, "r", encoding="utf-8") as f:
            scenes = json.load(f)
    except Exception as e:
        log.error(f"[SocialAssets] Job #{job_id}: Error leyendo script.json: {e}")
        return False

    # Extraer narración completa
    narrations = [s.get("narration", "") for s in scenes if s.get("narration")]
    if not narrations:
        log.warning(f"[SocialAssets] Job #{job_id}: No hay narración en el guion.")
        return False

    full_text = " ".join(narrations)[:3000]  # Limitar para no saturar el contexto del LLM

    try:
        from core.provider_manager import get_best, complete

        best_prov, best_model = get_best()
        if best_prov is None or best_model is None:
            log.warning(f"[SocialAssets] Job #{job_id}: No hay LLM disponible.")
            return False

        log.info(f"[SocialAssets] Job #{job_id}: Generando activos sociales con {best_prov.name}...")

        prompt = (
            f"Basado en este guion de video (idioma: {lang}), actúa como un Copywriter Experto "
            "y genera 3 piezas de contenido de alto impacto para redes sociales.\n\n"
            "GUION:\n"
            f"{full_text}\n\n"
            "Genera EXACTAMENTE en este formato (sin texto adicional antes ni después):\n\n"
            "--- TWITTER THREAD ---\n"
            "[Hilo de 3-5 tweets con gancho viral desde el primero. Usa emojis y saltos de línea. "
            "Cada tweet separado con una línea en blanco.]\n\n"
            "--- INSTAGRAM CAROUSEL ---\n"
            "[Texto para 5-7 diapositivas. Cada diapositiva: '🟦 SLIDE X: [texto corto y visual]']\n\n"
            "--- LINKEDIN POST ---\n"
            "[Post profesional con gancho fuerte, historia/valor y CTA claro. Máx 300 palabras.]\n"
        )

        messages = [
            {"role": "system", "content": "Eres un experto en Social Media Marketing y Copywriting viral."},
            {"role": "user", "content": prompt},
        ]

        result = complete(
            messages=messages,
            model=best_model,
            provider=best_prov.name,
            options={"temperature": 0.75, "max_tokens": 2048},
        )

        if not result or len(result.strip()) < 50:
            log.warning(f"[SocialAssets] Job #{job_id}: LLM devolvió respuesta vacía.")
            return False

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# Gravity AI — Activos Sociales | Job #{job_id}\n\n")
            f.write(result)

        log.info(f"[SocialAssets] Job #{job_id}: Activos guardados en {output_path}")
        return True

    except Exception as e:
        log.error(f"[SocialAssets] Job #{job_id}: Error inesperado: {e}")
        return False
