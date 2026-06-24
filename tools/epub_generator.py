import os
import sys
import re
import logging
import argparse

try:
    import markdown
    from ebooklib import epub
except ImportError:
    print("Falta instalar EbookLib o markdown: pip install EbookLib markdown")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("EpubGenerator")


def generate_epub(target_dir: str) -> str:
    """
    Convierte el archivo Markdown compilado de un directorio en un EPUB profesional.
    """
    target_dir = os.path.abspath(target_dir)
    if not os.path.exists(target_dir):
        logger.error(f"El directorio no existe: {target_dir}")
        return ""

    dir_name = os.path.basename(target_dir)

    # 1. Buscar el archivo MD maestro
    # Intentar buscar el que termine en _refinado.md o tenga el mismo nombre de la carpeta
    master_md = ""
    for file in os.listdir(target_dir):
        if file.endswith("_refinado.md"):
            master_md = os.path.join(target_dir, file)
            break

    if not master_md:
        fallback = os.path.join(target_dir, f"{dir_name}.md")
        if os.path.exists(fallback):
            master_md = fallback

    if not master_md or not os.path.exists(master_md):
        logger.error(f"No se encontró un archivo .md principal en {target_dir}")
        return ""

    logger.info(f"Procesando: {master_md}")

    with open(master_md, "r", encoding="utf-8") as f:
        content = f.read()

    # Extraer el título del H1 principal
    title_match = re.search(r"^#\s+(.+)$", content, flags=re.MULTILINE)
    book_title = (
        title_match.group(1).strip() if title_match else dir_name.replace("_", " ")
    )

    # Configurar el libro EPUB
    book = epub.EpubBook()
    book.set_identifier(f"gravity_id_{dir_name}")
    book.set_title(book_title)
    book.set_language("es")
    book.add_author("Gravity AI Engine")

    # Intentar inyectar portada
    cover_found = False
    for ext in [".png", ".jpg", ".jpeg", ".svg"]:
        cover_path = os.path.join(target_dir, f"cover{ext}")
        if os.path.exists(cover_path):
            with open(cover_path, "rb") as cf:
                book.set_cover(f"cover{ext}", cf.read())
            logger.info(f"Portada inyectada desde {cover_path}")
            cover_found = True
            break

    # CSS por defecto para KDP y E-readers
    style = """
    body { font-family: "Georgia", serif; line-height: 1.6; padding: 2em; text-align: justify; }
    h1 { text-align: center; font-size: 2em; margin-bottom: 1em; page-break-before: always; }
    h2 { font-size: 1.5em; margin-top: 1.5em; }
    p { margin-bottom: 1em; }
    """
    default_css = epub.EpubItem(
        uid="style_default",
        file_name="style/default.css",
        media_type="text/css",
        content=style,
    )
    book.add_item(default_css)

    # Dividir el contenido por "---" que es el separador de capítulos en los ensambladores
    sections = re.split(r"\n\s*---\s*\n", content)

    epub_chapters = []

    for i, sec_text in enumerate(sections):
        sec_text = sec_text.strip()
        if not sec_text:
            continue

        # Intentar extraer un título de capítulo para el ToC
        ch_title = f"Sección {i+1}"
        h1_match = re.search(r"^#\s+(.+)$", sec_text, flags=re.MULTILINE)
        h2_match = re.search(r"^##\s+(.+)$", sec_text, flags=re.MULTILINE)
        if h1_match:
            ch_title = h1_match.group(1).strip()
        elif h2_match:
            ch_title = h2_match.group(1).strip()

        # Convertir a HTML (XHTML estricto requerido por EPUB)
        html_content = markdown.markdown(
            sec_text, extensions=["tables"], output_format="xhtml"
        )

        # Empaquetar imágenes incrustadas en el capítulo
        for img_match in re.finditer(r'<img[^>]+src="([^"]+)"', html_content):
            img_src = img_match.group(1)
            if not img_src.startswith("http"):
                img_path = os.path.join(target_dir, img_src)
                if os.path.exists(img_path):
                    # Evitar duplicados si la misma imagen se usa varias veces
                    if not book.get_item_with_id(img_src):
                        try:
                            with open(img_path, "rb") as f:
                                # Suponemos png por el generador de pollinations, pero se podría inferir por extensión
                                ext = os.path.splitext(img_src)[1].lower()
                                mime = (
                                    "image/jpeg"
                                    if ext in [".jpg", ".jpeg"]
                                    else (
                                        "image/svg+xml"
                                        if ext == ".svg"
                                        else "image/png"
                                    )
                                )
                                img_item = epub.EpubImage(
                                    uid=img_src,
                                    file_name=img_src,
                                    media_type=mime,
                                    content=f.read(),
                                )
                                book.add_item(img_item)
                                logger.info(
                                    f"    Imagen secundaria empaquetada: {img_src}"
                                )
                        except Exception as e:
                            logger.error(
                                f"    Error empaquetando imagen {img_src}: {e}"
                            )

        # Envolver en HTML
        full_html = f"""<html xmlns="http://www.w3.org/1999/xhtml" lang="es">
<head>
<title>{ch_title}</title>
<link href="style/default.css" rel="stylesheet" type="text/css" />
</head>
<body>
{html_content}
</body>
</html>"""

        ch = epub.EpubHtml(title=ch_title, file_name=f"chap_{i:02d}.xhtml", lang="es")
        ch.content = full_html
        ch.add_item(default_css)
        book.add_item(ch)
        epub_chapters.append(ch)

    # Establecer la Tabla de Contenidos (ToC)
    book.toc = tuple(epub_chapters)

    # Añadir los archivos de navegación estándar de EPUB
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Establecer la espina dorsal del libro (orden de lectura)
    spine = ["nav"] + epub_chapters
    book.spine = spine

    # Exportar
    output_path = os.path.join(target_dir, f"{dir_name}.epub")
    epub.write_epub(output_path, book, {})
    logger.info(f"[EPUB COMPLETADO] {output_path}")

    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gravity EPUB Generator")
    parser.add_argument("target", help="Ruta al directorio de la obra")
    args = parser.parse_args()
    generate_epub(args.target)
