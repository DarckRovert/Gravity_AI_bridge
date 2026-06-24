"""
Gravity AI Bridge — Retry de Imágenes Fallidas
Lee el failed_images.json generado por book_refiner.py,
reintenta la generación con Pollinations (más pausas y reintentos),
inyecta el lore del proyecto, actualiza el Markdown y re-empaqueta el EPUB.

Uso:
    python tools/retry_failed_images.py <ruta_a_directorio_refinado>

Ejemplo:
    python tools/retry_failed_images.py ficcion_generada/Cenizas_del_Leviatan_Libro_3_refinado
"""

import os
import sys
import json
import time
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.visual_lore import inject_lore_to_prompt  # noqa: E402
from tools.pollinations_generator import generate as poll_gen  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("RetryImages")

# ─── Configuración de reintentos más agresiva que la original ─────────────────
MAX_RETRIES = 4  # Más intentos que los 2 del refiner original
RETRY_DELAY = 8.0  # Espera entre intentos (Pollinations se recupera si le damos tiempo)
INTER_IMG_WAIT = 5.0  # Pausa entre imágenes para no saturar la API


def _load_lore(refined_dir: str) -> dict:
    """
    Busca el lore_book.json:
    1. En el propio directorio refinado.
    2. En el directorio hermano sin sufijo '_refinado' (donde está el borrador original).
    3. Fallback vacío si no encuentra nada.
    """
    # Candidato 1: mismo directorio
    candidate1 = os.path.join(refined_dir, "lore_book.json")
    if os.path.exists(candidate1):
        with open(candidate1, "r", encoding="utf-8") as f:
            logger.info(f"Lore cargado desde: {candidate1}")
            return json.load(f)

    # Candidato 2: directorio hermano sin '_refinado'
    parent = os.path.dirname(refined_dir)
    base_name = os.path.basename(refined_dir)
    draft_name = base_name.replace("_refinado", "").replace("_refined", "")
    candidate2 = os.path.join(parent, draft_name, "lore_book.json")
    if os.path.exists(candidate2):
        with open(candidate2, "r", encoding="utf-8") as f:
            logger.info(f"Lore cargado desde: {candidate2}")
            return json.load(f)

    logger.warning(
        "No se encontró lore_book.json. Las imágenes se generarán sin descripción de personajes."
    )
    return {
        "global_style": "cinematic, hyperrealistic, highly detailed",
        "characters": {},
    }


def _retry_single(entry: dict, refined_dir: str, lore_data: dict) -> bool:
    """
    Intenta generar una sola imagen fallida con reintentos extendidos.
    Devuelve True si tuvo éxito.
    """
    img_filename = entry["img_filename"]
    img_path = os.path.join(refined_dir, img_filename)
    base_prompt = entry["base_prompt"]
    char_seed = entry.get("char_seed")  # Semilla anclada al personaje principal

    # Re-inyectar el lore con la nueva versión del inject_lore_to_prompt mejorado
    final_prompt = inject_lore_to_prompt(lore_data, base_prompt)

    NEGATIVE_PROMPT = (
        "text, watermark, signature, logo, blurry, low quality, deformed hands, "
        "extra limbs, bad anatomy, ugly, cartoon, anime, letters, words, "
        "oversaturated, overexposed"
    )

    logger.info(f"Reintentando: {img_filename}")
    logger.info(f"  Prompt ({len(final_prompt)} chars): {final_prompt[:120]}...")

    for attempt in range(1, MAX_RETRIES + 1):
        logger.info(f"  Intento {attempt}/{MAX_RETRIES}...")
        time.sleep(RETRY_DELAY)

        result = poll_gen(
            prompt=final_prompt,
            output_path=img_path,
            width=1024,
            height=1024,
            seed=char_seed,
            enhance=False,
            negative_prompt=NEGATIVE_PROMPT,
        )

        if result.get("success"):
            logger.info(f"  ✅ Éxito en intento {attempt}: {img_filename}")
            return True
        else:
            logger.warning(
                f"  Intento {attempt} fallido: {result.get('error', 'Desconocido')}"
            )

    logger.error(
        f"  ❌ Imagen {img_filename} no pudo generarse tras {MAX_RETRIES} intentos."
    )
    return False


def _update_markdown(refined_dir: str, img_filename: str) -> None:
    """
    Reemplaza el comentario placeholder <!-- FAILED_IMAGE:filename.png -->
    con la referencia de imagen correcta en todos los archivos .md del directorio.
    """
    placeholder = f"<!-- FAILED_IMAGE:{img_filename} -->"
    replacement = f"\n\n![Ilustración]({img_filename})\n\n"

    for fname in os.listdir(refined_dir):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(refined_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        if placeholder in content:
            updated = content.replace(placeholder, replacement)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(updated)
            logger.info(f"  Markdown actualizado: {fname}")


def _repackage_epub(refined_dir: str) -> None:
    """
    Re-empaqueta el EPUB después de actualizar el Markdown.
    """
    try:
        from tools.epub_generator import generate_epub

        result = generate_epub(refined_dir)
        logger.info(f"EPUB re-empaquetado: {result}")
    except Exception as e:
        logger.error(f"No se pudo re-empaquetar EPUB: {e}")
        logger.info(
            "Puedes hacerlo manualmente con: python tools/epub_generator.py <directorio_refinado>"
        )


def retry_failed_images(refined_dir: str) -> None:
    """Punto de entrada principal."""
    refined_dir = os.path.abspath(refined_dir)

    if not os.path.isdir(refined_dir):
        logger.error(f"El directorio no existe: {refined_dir}")
        sys.exit(1)

    failed_log_path = os.path.join(refined_dir, "failed_images.json")
    if not os.path.exists(failed_log_path):
        logger.info(
            "No hay imágenes fallidas registradas en este directorio. ¡Todo está perfecto!"
        )
        return

    with open(failed_log_path, "r", encoding="utf-8") as f:
        failed_entries = json.load(f)

    if not failed_entries:
        logger.info(
            "El archivo de recuperación está vacío. No hay nada que reintentar."
        )
        return

    logger.info(
        f"Se encontraron {len(failed_entries)} imágenes fallidas en '{refined_dir}'."
    )
    lore_data = _load_lore(refined_dir)

    recovered = []
    still_failing = []

    for entry in failed_entries:
        success = _retry_single(entry, refined_dir, lore_data)
        if success:
            _update_markdown(refined_dir, entry["img_filename"])
            recovered.append(entry["img_filename"])
        else:
            still_failing.append(entry)

        time.sleep(INTER_IMG_WAIT)

    # Actualizar el archivo de recuperación (solo quedan las que siguen fallando)
    with open(failed_log_path, "w", encoding="utf-8") as f:
        json.dump(still_failing, f, indent=2, ensure_ascii=False)

    logger.info("\n--- RESUMEN ---")
    logger.info(f"  ✅ Recuperadas: {len(recovered)}")
    logger.info(f"  ❌ Aún fallidas: {len(still_failing)}")

    if recovered:
        logger.info("Re-empaquetando EPUB con las nuevas imágenes...")
        _repackage_epub(refined_dir)

    if still_failing:
        logger.warning(
            "Las imágenes persistentemente fallidas permanecen en failed_images.json."
        )
        logger.warning(
            "Puedes volver a ejecutar este script más tarde para reintentarlas."
        )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    target = sys.argv[1]
    retry_failed_images(target)
