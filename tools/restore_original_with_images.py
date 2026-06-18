"""
Script para restaurar la historia ORIGINAL sin que el LLM altere ni una sola letra del texto,
pero inyectando creativamente imágenes generadas en momentos clave de cada capítulo.
"""
import os
import sys
import json
import logging
import re
from typing import List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core import provider_manager, image_router
from tools.book_refiner import _render_html, _assemble_book, _detect_caps

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RestoreFiction")

FICTION_DIR = os.path.join(BASE_DIR, "ficcion_generada")

def generate_image_prompt(paragraph_text: str) -> str:
    """Usa el LLM para generar un prompt de imagen ultra-detallado basado en un párrafo."""
    sys_prompt = f"""Eres un director de arte cyberpunk/neo-noir.
Lee este párrafo y genera UN SOLO PROMPT EN INGLÉS para un modelo generador de imágenes (Flux/Midjourney).
El prompt debe describir visualmente la escena, los personajes, la iluminación y el entorno.
No incluyas texto, ni logos. Usa términos como "Cinematic, photorealistic, Unreal Engine 5, 8k, volumetric lighting".
PÁRRAFO:
{paragraph_text}

DEVUELVE ÚNICAMENTE EL PROMPT EN INGLÉS, sin comillas ni introducciones."""
    
    messages = [{"role": "user", "content": sys_prompt}]
    resp = provider_manager.complete(messages)
    return resp.strip() if resp else "Cinematic cyberpunk scene, neo-noir, dark atmosphere, 8k"

def process_chapter(original_cap_path: str, out_dir: str, cap_name: str, book_name: str):
    with open(original_cap_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Dividir en párrafos
    paragraphs = text.split("\n\n")
    if len(paragraphs) < 5:
        paragraphs_to_illustrate = [len(paragraphs)//2]
    else:
        # Ilustrar el primer tercio y el último tercio
        paragraphs_to_illustrate = [max(1, len(paragraphs)//4), min(len(paragraphs)-2, (len(paragraphs)//4)*3)]

    new_paragraphs = []
    for i, p in enumerate(paragraphs):
        if i in paragraphs_to_illustrate and len(p.strip()) > 50:
            logger.info(f"    Generando prompt de imagen para {cap_name} (sección {i})...")
            img_prompt = generate_image_prompt(p)
            
            # Generar la imagen real
            import hashlib
            prompt_hash = hashlib.md5(img_prompt.encode()).hexdigest()[:8]
            img_filename = f"img_{cap_name}_{prompt_hash}.png"
            img_out_path = os.path.join(out_dir, img_filename)
            
            logger.info(f"    Generando imagen: {img_filename}")
            res = image_router.generate(
                prompt=img_prompt,
                output_path=img_out_path,
                width=832,
                height=512,
                title=f"{book_name} - {cap_name}"
            )
            
            if res.get("success"):
                new_paragraphs.append(f"![Escena ilustrada]({img_filename})")
            else:
                logger.warning(f"    Fallo al generar imagen: {res.get('error')}")

        new_paragraphs.append(p)

    # Reensamblar y guardar
    new_text = "\n\n".join(new_paragraphs)
    out_cap_path = os.path.join(out_dir, cap_name + ".md")
    with open(out_cap_path, "w", encoding="utf-8") as f:
        f.write(new_text)

def main():
    books = [1, 2, 3]
    for b in books:
        book_dir = os.path.join(FICTION_DIR, f"Cenizas_del_Leviatan_Libro_{b}")
        out_dir = book_dir + "_refinado"
        
        if not os.path.exists(book_dir):
            continue
            
        logger.info(f"=== RESTAURANDO E ILUSTRANDO LIBRO {b} ===")
        os.makedirs(out_dir, exist_ok=True)
        
        # Copiar portada original o SVG si no existe en refinado
        for file in ["cover.png", "cover.svg", "lore_book.json", "glosario.md"]:
            src = os.path.join(book_dir, file)
            dst = os.path.join(out_dir, file)
            if os.path.exists(src) and not os.path.exists(dst):
                import shutil
                shutil.copy2(src, dst)

        caps = _detect_caps(book_dir)
        for cap_path in caps:
            cap_name = os.path.basename(cap_path).replace(".md", "")
            logger.info(f"  Procesando {cap_name}...")
            process_chapter(cap_path, out_dir, cap_name, f"Libro {b}")

        # Ensamblar libro y HTML
        title = f"Cenizas del Leviatán Libro {b} (Original Ilustrado)"
        ref_caps = _detect_caps(out_dir)
        assembled = _assemble_book(out_dir, title, sorted(ref_caps, key=lambda p: int(re.search(r'cap_(\d+)', p).group(1))))
        
        book_md_path = os.path.join(out_dir, f"Cenizas_del_Leviatan_Libro_{b}_refinado.md")
        with open(book_md_path, "w", encoding="utf-8") as f:
            f.write(assembled)
            
        html_path = book_md_path.replace(".md", ".html")
        _render_html(out_dir, assembled, html_path, title)
        logger.info(f"  HTML generado: {html_path}")

if __name__ == "__main__":
    main()
