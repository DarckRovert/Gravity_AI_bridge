import os
import re
import shutil
import glob
import logging
from tools.epub_generator import generate_epub

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("RebuildV1")


def find_image_for_chapter(base_name: str, cap_num: str) -> str:
    """Busca la imagen del capítulo en _definitivo o _refinado"""
    # Intentar buscar en _definitivo primero
    def_dir = f"ficcion_generada/{base_name}_definitivo"
    imgs = glob.glob(os.path.join(def_dir, f"img_cap_{cap_num}_*.png"))
    if imgs:
        return imgs[0]

    # Intentar buscar en _refinado si no está
    ref_dir = f"ficcion_generada/{base_name}_refinado"
    imgs = glob.glob(os.path.join(ref_dir, f"img_cap_{cap_num}_*.png"))
    if imgs:
        return imgs[0]

    return ""


def rebuild_book(base_name: str):
    orig_dir = f"ficcion_generada/{base_name}"
    def_dir = f"ficcion_generada/{base_name}_definitivo"

    if not os.path.exists(orig_dir):
        logger.error(f"No existe el directorio original: {orig_dir}")
        return

    os.makedirs(def_dir, exist_ok=True)

    # Copiar portada
    cover_src = os.path.join(orig_dir, "cover.png")
    if os.path.exists(cover_src):
        shutil.copy2(cover_src, os.path.join(def_dir, "cover.png"))

    master_md_path = os.path.join(def_dir, f"{base_name}_definitivo.md")

    book_title = base_name.replace("_", " ")

    # Patron para inyectar la imagen justo debajo del titulo del capitulo
    pattern = re.compile(
        r"^(#+.*cap[ií]tulo\s+(\d+)[^\n]*\n)", re.IGNORECASE | re.MULTILINE
    )

    with open(master_md_path, "w", encoding="utf-8") as f_out:
        # Cabecera
        f_out.write(
            f"# {book_title}\n\n*Versión 1 Original Pura con Ilustraciones*\n\n"
        )
        f_out.write("## Índice\n\n---\n\n")

        # Ensamblar capítulos del 1 al 99
        for i in range(1, 100):
            cap_file = os.path.join(orig_dir, f"cap_{i}.md")
            if not os.path.exists(cap_file):
                # Probablemente terminaron los capítulos
                continue

            logger.info(f"Procesando {cap_file}...")
            with open(cap_file, "r", encoding="utf-8") as f_in:
                content = f_in.read()

            # Buscar imagen
            img_src = find_image_for_chapter(base_name, str(i))
            if img_src:
                img_name = os.path.basename(img_src)
                dest_img = os.path.join(def_dir, img_name)
                # Copiar imagen si no está ahí ya
                if os.path.abspath(img_src) != os.path.abspath(dest_img):
                    shutil.copy2(img_src, dest_img)

                # Inyectar
                def inject_image(match):
                    full_match = match.group(0)
                    injection = f"\n\n![Ilustración]({img_name})\n\n"
                    return full_match + injection

                content = pattern.sub(inject_image, content)
                logger.info(f"  Imagen {img_name} inyectada en Capítulo {i}")
            else:
                logger.warning(f"  No se encontró imagen para el Capítulo {i}")

            # Escribir contenido y SEPARADOR DE PÁGINA
            f_out.write(content.strip() + "\n\n---\n\n")

        # Añadir glosario si existe
        glosario_file = os.path.join(orig_dir, "glosario.md")
        if os.path.exists(glosario_file):
            logger.info("Añadiendo glosario...")
            with open(glosario_file, "r", encoding="utf-8") as f_in:
                content = f_in.read()
                f_out.write(content.strip() + "\n\n---\n\n")

    logger.info(f"Texto maestro V1 reconstruido en: {master_md_path}")

    # Generar EPUB
    logger.info("Generando EPUB...")
    epub_path = generate_epub(def_dir)
    if epub_path:
        logger.info(f"EPUB final generado exitosamente: {epub_path}")


def main():
    books = [
        "Cenizas_del_Leviatan_Libro_1",
        "Cenizas_del_Leviatan_Libro_2",
        "Cenizas_del_Leviatan_Libro_3",
    ]
    for book in books:
        logger.info(f"=== Reconstruyendo {book} ===")
        rebuild_book(book)


if __name__ == "__main__":
    main()
