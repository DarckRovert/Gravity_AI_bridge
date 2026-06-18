import os
import re
import shutil
import logging
from tools.epub_generator import generate_epub

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Merger")

def process_book(book_num: int):
    base_name = f"Cenizas_del_Leviatan_Libro_{book_num}"
    orig_dir = os.path.join("f:\\Gravity_AI_bridge\\ficcion_generada", base_name)
    ref_dir = os.path.join("f:\\Gravity_AI_bridge\\ficcion_generada", f"{base_name}_refinado")
    def_dir = os.path.join("f:\\Gravity_AI_bridge\\ficcion_generada", f"{base_name}_definitivo")

    orig_md = os.path.join(orig_dir, f"{base_name}.md")
    
    if not os.path.exists(orig_md):
        logger.error(f"No se encontró el original: {orig_md}")
        return

    os.makedirs(def_dir, exist_ok=True)
    def_md = os.path.join(def_dir, f"{base_name}_definitivo.md")

    # Leer texto original
    with open(orig_md, "r", encoding="utf-8") as f:
        content = f.read()

    # Copiar portada si existe
    cover_src = os.path.join(ref_dir, "cover.png")
    if not os.path.exists(cover_src):
        cover_src = os.path.join(orig_dir, "cover.png")
    if os.path.exists(cover_src):
        shutil.copy(cover_src, os.path.join(def_dir, "cover.png"))

    # Buscar todas las imágenes generadas en el refinado
    images = {}
    if os.path.exists(ref_dir):
        for file in os.listdir(ref_dir):
            if file.startswith("img_cap_") and file.endswith(".png"):
                # Extraer el numero de capitulo
                match = re.search(r"img_cap_(\d+)_", file)
                if match:
                    cap_num = int(match.group(1))
                    images[cap_num] = file

    # Separar el contenido original por capítulos
    # El patrón es ## CAPÍTULO X
    # Vamos a usar una función de reemplazo para inyectar la imagen después de los asteriscos ***
    
    def inject_image(match):
        full_match = match.group(0)
        cap_num_str = match.group(2)
        cap_num = int(cap_num_str)
        
        if cap_num in images:
            img_file = images[cap_num]
            # Copiar imagen al directorio definitivo
            src_img = os.path.join(ref_dir, img_file)
            dst_img = os.path.join(def_dir, img_file)
            shutil.copy(src_img, dst_img)
            # Inyectar imagen después del título del capítulo
            injection = f"\n\n![Ilustración]({img_file})\n\n"
            return full_match + injection
        return full_match

    # Buscamos: #, ##, ### Capítulo X... o # Titulo: Capítulo X
    pattern = re.compile(r"^(#+.*cap[ií]tulo\s+(\d+)[^\n]*\n)", re.IGNORECASE | re.MULTILINE)
    
    new_content = pattern.sub(inject_image, content)

    with open(def_md, "w", encoding="utf-8") as f:
        f.write(new_content)

    logger.info(f"Texto fusionado guardado en {def_md}")

    # Empaquetar
    generate_epub(def_dir)

if __name__ == "__main__":
    for i in range(1, 4):
        process_book(i)
