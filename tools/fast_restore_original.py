"""
Restaura rápidamente la historia a los textos originales (sin reescritura del LLM),
extrayendo las imágenes que el LLM ya había generado en _refinado y re-inyectándolas
en el texto original. Toma segundos y preserva el 100% de la historia y el arte.
"""

import os
import sys
import re
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools.book_refiner import _render_html, _assemble_book, _detect_caps  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("FastRestore")

FICTION_DIR = os.path.join(BASE_DIR, "ficcion_generada")


def get_images_from_md(md_text: str) -> list:
    """Extrae todas las etiquetas ![...](...) de un texto."""
    return re.findall(r"!\[.*?\]\(.*?\)", md_text)


def main():
    for b in [1, 2, 3]:
        orig_dir = os.path.join(FICTION_DIR, f"Cenizas_del_Leviatan_Libro_{b}")
        ref_dir = orig_dir + "_refinado"

        if not os.path.exists(orig_dir) or not os.path.exists(ref_dir):
            continue

        logger.info(f"=== RESTAURANDO TEXTO ORIGINAL DEL LIBRO {b} ===")

        orig_caps = _detect_caps(orig_dir)
        for cap_path in orig_caps:
            cap_name = os.path.basename(cap_path)
            ref_cap_path = os.path.join(ref_dir, cap_name)

            # Leer original puro
            with open(cap_path, "r", encoding="utf-8") as f:
                orig_text = f.read()

            # Leer refinado "arruinado" solo para robarle las imágenes
            images = []
            if os.path.exists(ref_cap_path):
                with open(ref_cap_path, "r", encoding="utf-8") as f:
                    ref_text = f.read()
                images = get_images_from_md(ref_text)

            # Inyectar imágenes en el texto original (al principio o distribuidas)
            paragraphs = orig_text.split("\n\n")
            if images:
                # Distribuir las imágenes a lo largo del texto
                step = max(1, len(paragraphs) // (len(images) + 1))
                for idx, img_tag in enumerate(images):
                    insert_pos = step * (idx + 1)
                    if insert_pos < len(paragraphs):
                        paragraphs.insert(insert_pos, img_tag)
                    else:
                        paragraphs.append(img_tag)

            # Sobrescribir en refinado con el texto puramente original + imágenes
            new_text = "\n\n".join(paragraphs)
            with open(ref_cap_path, "w", encoding="utf-8") as f:
                f.write(new_text)

            logger.info(
                f"  {cap_name} restaurado (con {len(images)} imágenes inyectadas)."
            )

        # Ensamblar libro y HTML
        title = f"Cenizas del Leviatán Libro {b} (Original Ilustrado)"
        ref_caps = _detect_caps(ref_dir)
        assembled = _assemble_book(
            ref_dir,
            title,
            sorted(ref_caps, key=lambda p: int(re.search(r"cap_(\d+)", p).group(1))),
        )

        book_md_path = os.path.join(
            ref_dir, f"Cenizas_del_Leviatan_Libro_{b}_refinado.md"
        )
        with open(book_md_path, "w", encoding="utf-8") as f:
            f.write(assembled)

        html_path = book_md_path.replace(".md", ".html")
        _render_html(ref_dir, assembled, html_path, title)
        logger.info(f"  HTML generado: {html_path}")


if __name__ == "__main__":
    main()
