"""
Script para purgar imágenes defectuosas de Pollinations,
e integrar el arte Ultra-Premium generado con Imagen 3.
"""

import os
import sys
import glob
import re
import shutil
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools.book_refiner import _render_html, _assemble_book, _detect_caps

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ArtCleanup")

FICTION_DIR = os.path.join(BASE_DIR, "ficcion_generada")

# Mapeos estáticos generados por el agente
NEW_COVERS = {
    1: r"C:\Users\darck\.gemini\antigravity-ide\brain\a1e23264-d6f5-492c-b198-03617c477d77\cover_libro_1_1781721694566.png",
    2: r"C:\Users\darck\.gemini\antigravity-ide\brain\a1e23264-d6f5-492c-b198-03617c477d77\cover_libro_2_1781721705689.png",
    3: r"C:\Users\darck\.gemini\antigravity-ide\brain\a1e23264-d6f5-492c-b198-03617c477d77\cover_libro_3_1781721717018.png",
}
FRONTISPIECES = {
    1: r"C:\Users\darck\.gemini\antigravity-ide\brain\a1e23264-d6f5-492c-b198-03617c477d77\arte_kaelen_1781721728307.png",
    2: r"C:\Users\darck\.gemini\antigravity-ide\brain\a1e23264-d6f5-492c-b198-03617c477d77\arte_lyra_1781721739620.png",
    3: r"C:\Users\darck\.gemini\antigravity-ide\brain\a1e23264-d6f5-492c-b198-03617c477d77\arte_architect_1781721749377.png",
}


def remove_glitchy_images(ref_dir: str):
    """Borra físicamente los pngs malos de Pollinations."""
    bad_pngs = glob.glob(os.path.join(ref_dir, "img_cap_*.png"))
    for png in bad_pngs:
        os.remove(png)
        logger.info(f"  Eliminado: {os.path.basename(png)}")


def clean_markdown_tags(ref_dir: str):
    """Elimina las etiquetas ![...](img_cap_...) de los archivos .md"""
    for cap_path in _detect_caps(ref_dir):
        with open(cap_path, "r", encoding="utf-8") as f:
            text = f.read()

        # Remover las lineas de imagen rotas
        cleaned_text = re.sub(r"!\[.*?\]\(img_cap_.*?\.png\)", "", text)
        # Limpiar lineas vacías consecutivas causadas por remover las imagenes
        cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text).strip()

        with open(cap_path, "w", encoding="utf-8") as f:
            f.write(cleaned_text)


def install_premium_art(b: int, ref_dir: str):
    """Copia la portada y el frontispicio premium, e inyecta el frontispicio en cap_1."""
    # 1. Copiar Cover
    cover_src = NEW_COVERS.get(b)
    if cover_src and os.path.exists(cover_src):
        shutil.copy2(cover_src, os.path.join(ref_dir, "cover.png"))
        logger.info("  Portada premium instalada.")

    # 2. Copiar Frontispicio
    front_src = FRONTISPIECES.get(b)
    if front_src and os.path.exists(front_src):
        shutil.copy2(front_src, os.path.join(ref_dir, "frontispiece.png"))
        logger.info("  Arte Conceptual premium instalado.")

        # 3. Inyectar Frontispicio al inicio del cap_1.md
        cap1_path = os.path.join(ref_dir, "cap_1.md")
        if os.path.exists(cap1_path):
            with open(cap1_path, "r", encoding="utf-8") as f:
                text = f.read()

            # Inyectar la imagen justo despues del titulo principal (primer salto de linea)
            lines = text.split("\n")
            if lines:
                new_lines = (
                    lines[:2]
                    + ["\n![Arte Conceptual Principal](frontispiece.png)\n"]
                    + lines[2:]
                )
                with open(cap1_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(new_lines))


def main():
    for b in [1, 2, 3]:
        ref_dir = os.path.join(FICTION_DIR, f"Cenizas_del_Leviatan_Libro_{b}_refinado")
        if not os.path.exists(ref_dir):
            continue

        logger.info(f"=== PURGA Y MEJORA VISUAL LIBRO {b} ===")

        remove_glitchy_images(ref_dir)
        clean_markdown_tags(ref_dir)
        install_premium_art(b, ref_dir)

        # Reensamblar y generar HTML definitivo
        title = f"Cenizas del Leviatán Libro {b}"
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
        logger.info("  HTML definitivo renderizado.\n")


if __name__ == "__main__":
    main()
