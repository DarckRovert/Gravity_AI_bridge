"""
Script puntual para generar el Capítulo 8 (faltante) del Libro 1.
Usa el historial de continuidad existente + la escaleta + lore_bible como contexto.
"""

import os
import sys
import json
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools.fiction_writer import GravityFictionAuthor

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("GenerateCap8")

BOOK_NAME = "Cenizas_del_Leviatan_Libro_1"
BOOK_DIR = os.path.join(BASE_DIR, "ficcion_generada", BOOK_NAME)
LORE_FILE = os.path.join(BASE_DIR, "lore_bible.md")


def main():
    # Verificar estado
    progress_file = os.path.join(BOOK_DIR, "progreso_metadata.json")
    cap8_file = os.path.join(BOOK_DIR, "cap_8.md")

    with open(progress_file, "r", encoding="utf-8") as f:
        prog = json.load(f)

    last_cap = prog.get("ultimo_capitulo_completado", 0)
    logger.info(f"Estado actual: último capítulo completado = {last_cap}")

    if last_cap >= 8:
        cap8_content = open(cap8_file, encoding="utf-8").read().strip()
        if len(cap8_content) > 100:
            logger.info("cap_8.md ya tiene contenido. Nada que hacer.")
            return
        logger.warning("cap_8.md existe pero está vacío. Generando...")

    # Cargar contexto
    with open(os.path.join(BOOK_DIR, "2_escaleta.json"), "r", encoding="utf-8") as f:
        escaleta = json.load(f)

    # La escaleta puede ser lista directa o {"capitulos": [...]}
    if isinstance(escaleta, dict):
        escaleta = escaleta.get("capitulos", [])

    cap8_data = next((c for c in escaleta if c.get("numero") == 8), None)
    if not cap8_data:
        logger.error("No se encontró el capítulo 8 en la escaleta.")
        return

    logger.info(
        f"Cap 8: {cap8_data.get('titulo')} — {cap8_data.get('resumen_eventos', '')[:100]}..."
    )

    with open(os.path.join(BOOK_DIR, "1_sinopsis_base.md"), "r", encoding="utf-8") as f:
        synopsis = f.read()

    with open(
        os.path.join(BOOK_DIR, "historial_continuidad.md"), "r", encoding="utf-8"
    ) as f:
        history = f.read()

    full_outline_text = "\n".join(
        [
            f"Cap {c.get('numero')}: {c.get('titulo')} — {c.get('resumen_eventos', '')[:150]}"
            for c in escaleta
        ]
    )

    # Inicializar el motor con la lore_bible
    author = GravityFictionAuthor(lore_file=LORE_FILE)

    # También cargar el lore_book.json visual
    lore_book_path = os.path.join(BOOK_DIR, "lore_book.json")
    if os.path.exists(lore_book_path):
        with open(lore_book_path, "r", encoding="utf-8") as f:
            lore_book = json.load(f)
        # Inyectar en el lore_bible del author como contexto adicional
        char_context = "\n".join(
            [
                f"## {name}\n{desc}"
                for name, desc in lore_book.get("characters", {}).items()
            ]
        )
        author.lore_bible += (
            f"\n\n## DESCRIPCIONES VISUALES FIJAS DE PERSONAJES\n{char_context}"
        )

    logger.info("Generando Capítulo 8...")
    chapter_text = author._write_chapter(
        cap8_data, synopsis, full_outline_text, history
    )

    if not chapter_text or len(chapter_text.strip()) < 100:
        logger.error(
            f"Generación fallida: capítulo vacío ({len(chapter_text.strip() if chapter_text else '')} chars)."
        )
        return

    logger.info(
        f"Capítulo generado: {len(chapter_text)} chars. Aplicando auto-edición..."
    )
    chapter_text = author._review_and_revise_chapter(
        chapter_text, author.lore_bible, history
    )

    # Guardar cap_8.md
    with open(cap8_file, "w", encoding="utf-8") as f:
        f.write(chapter_text)
    logger.info(f"cap_8.md guardado: {len(chapter_text)} chars.")

    # Actualizar progreso
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump({"ultimo_capitulo_completado": 8, "total": 8}, f)
    logger.info("progreso_metadata.json actualizado a cap 8/8.")

    # Reconstruir libro maestro
    book_md_path = os.path.join(BOOK_DIR, f"{BOOK_NAME}.md")
    html_path = os.path.join(BOOK_DIR, f"{BOOK_NAME}.html")

    logger.info("Reconstruyendo libro maestro .md...")
    with open(book_md_path, "w", encoding="utf-8") as f:
        f.write(
            f"# {BOOK_NAME.replace('_', ' ')}\n\n*Novela generada por Gravity Fiction Engine*\n\n"
        )
        f.write("## Índice\n")
        for c in escaleta:
            c_title = c.get("titulo", "")
            import urllib.parse

            anchor = "#" + urllib.parse.quote(
                c_title.lower().replace(" ", "-").replace(":", "")
            )
            f.write(f"{c.get('numero')}. [{c_title}]({anchor})\n")
        f.write("\n---\n\n")
        for i in range(1, 9):
            cf_path = os.path.join(BOOK_DIR, f"cap_{i}.md")
            if os.path.exists(cf_path):
                content = open(cf_path, "r", encoding="utf-8").read().strip()
                if content:
                    f.write(content + "\n\n---\n\n")
        # Glosario
        glosario_path = os.path.join(BOOK_DIR, "glosario.md")
        if os.path.exists(glosario_path):
            f.write(open(glosario_path, "r", encoding="utf-8").read() + "\n\n---\n\n")

    logger.info(f"Libro maestro reconstruido: {book_md_path}")

    # Re-renderizar HTML con CSS neo-noir
    try:
        from tools.book_refiner import _render_html

        md_content = open(book_md_path, "r", encoding="utf-8").read()
        _render_html(BOOK_DIR, md_content, html_path, BOOK_NAME.replace("_", " "))
        logger.info(f"HTML neo-noir generado: {html_path}")
    except Exception as e:
        logger.warning(f"No se pudo generar HTML: {e}")

    logger.info("=== GENERACIÓN CAP_8 COMPLETADA ===")
    logger.info(f"Archivo: {cap8_file}")
    logger.info(f"Longitud: {len(chapter_text)} caracteres")


if __name__ == "__main__":
    main()
