"""
Publicador Universal de Novelas.
Escanea automáticamente cualquier libro en el directorio ficcion_generada/,
genera prompts de portada dinámicos basados en la sinopsis usando el LLM,
y aplica el refinamiento seguro (modo publish) para empaquetar en HTML Neo-Noir.

Uso:
    python tools/publish.py                      # Publica todos los libros que falten
    python tools/publish.py --project "Nombre"   # Publica solo las carpetas que coincidan
    python tools/publish.py --force              # Fuerza a re-procesar todo
"""
import os
import sys
import json
import logging
import argparse
import shutil
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools.book_refiner import BookRefiner, _render_html, _detect_caps, _load_file, _assemble_book
from core import image_router, provider_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Publisher")

FICTION_DIR = os.path.join(BASE_DIR, "ficcion_generada")


def _generate_dynamic_cover_prompt(book_dir_path: str) -> str:
    """Lee la sinopsis del libro y pide al LLM un prompt visual en inglés para la portada."""
    synopsis = (
        _load_file(os.path.join(book_dir_path, "1_contexto_base.md")) or
        _load_file(os.path.join(book_dir_path, "1_sinopsis_base.md")) or ""
    )
    
    if not synopsis.strip():
        logger.warning("  No se encontró sinopsis. Usando prompt genérico.")
        return "Cinematic book cover, photorealistic, 8k, dark atmospheric aesthetic, no text, no letters."

    sys_prompt = f"""Eres un director de arte experimentado. 
Lee la siguiente sinopsis de un libro y genera UN SOLO PROMPT EN INGLÉS, corto y descriptivo, para generar una portada fotorrealista (estilo Midjourney/Flux).
Debe mencionar la estética, iluminación y elementos principales.
IMPORTANTE: Termina el prompt indicando que no haya texto. Ej: "Cinematic, photorealistic, Unreal Engine 5, 8k, no text, no letters."

SINOPSIS:
{synopsis[:1500]}

DEVUELVE ÚNICAMENTE EL PROMPT EN INGLÉS, sin comillas, ni explicaciones."""

    messages = [{"role": "user", "content": sys_prompt}]
    
    try:
        resp = provider_manager.complete(messages)
        import re
        if resp:
            resp = re.sub(r'<think>.*?</think>', '', resp, flags=re.DOTALL).strip()
            if '<think>' in resp:
                resp = re.sub(r'<think>.*', '', resp, flags=re.DOTALL).strip()
        prompt = resp.strip() if resp else ""
        if prompt:
            return prompt
    except Exception as e:
        logger.error(f"  Fallo al contactar LLM para prompt de portada: {e}")
        
    return "Cinematic book cover, photorealistic, 8k, dark atmospheric aesthetic, no text, no letters."


def fix_portada(book_dir_path: str, force: bool = False) -> bool:
    """Asegura que el libro tenga una portada real (cover.png) autogenerada si falta."""
    cover_png = os.path.join(book_dir_path, "cover.png")

    if not force and os.path.exists(cover_png) and os.path.getsize(cover_png) >= 50_000:
        logger.info(f"  Portada válida detectada: cover.png ({os.path.getsize(cover_png) // 1024} KB)")
        return True

    svg_path = os.path.join(book_dir_path, "cover.svg")
    if os.path.exists(svg_path):
        logger.info("  Removiendo placeholder cover.svg...")
        os.remove(svg_path)

    logger.info("  Analizando trama para generar prompt de portada...")
    cover_prompt = _generate_dynamic_cover_prompt(book_dir_path)
    logger.info(f"  Prompt generado: {cover_prompt[:100]}...")

    logger.info("  Generando portada via ImageRouter...")
    result = image_router.generate(
        prompt=cover_prompt,
        output_path=cover_png,
        width=832,
        height=1216,
        title=os.path.basename(book_dir_path).replace("_", " "),
    )
    
    if result.get("success"):
        logger.info(f"  Portada generada exitosamente → {cover_png}")
        return True
    else:
        logger.warning(f"  Fallo al generar portada: {result.get('error', 'unknown')}")
        return False


def run_rewrite_publish(book_dir_path: str, force: bool = False) -> str:
    """Ejecuta el formateo seguro sobre un libro y retorna el path del resultado."""
    refiner = BookRefiner()
    logger.info(f"\n{'='*60}")
    logger.info(f"PUBLICANDO: {os.path.basename(book_dir_path)}")
    logger.info(f"{'='*60}")

    out_dir = book_dir_path.rstrip("/\\") + "_refinado"
    
    # Si no hay force y el html ya existe y es reciente, podríamos saltarlo,
    # pero el refiner maneja el progreso interno.
    
    result_path = refiner.rewrite(
        book_dir=book_dir_path,
        depth="publish", # MODO 100% SEGURO (Sin LLM)
        output_suffix="_refinado",
        start_chapter=1,
    )
    return result_path


def rerender_html_refinado(book_dir_path: str, out_suffix: str = "_refinado"):
    """Re-renderiza el HTML del directorio refinado con el CSS neo-noir actualizado."""
    out_dir = book_dir_path.rstrip("/\\") + out_suffix
    if not os.path.isdir(out_dir):
        logger.warning(f"  Directorio publicable no encontrado: {out_dir}")
        return

    title = os.path.basename(out_dir).replace("_", " ")
    caps = _detect_caps(out_dir)
    if not caps:
        logger.warning(f"  No se encontraron capítulos en {out_dir}")
        return

    assembled = _assemble_book(
        out_dir,
        title,
        sorted(caps, key=lambda p: int(re.search(r'cap_(\d+)', p).group(1)))
    )

    base_name = os.path.basename(book_dir_path)
    html_path = os.path.join(out_dir, f"{base_name}_refinado.html")
    _render_html(out_dir, assembled, html_path, title)
    logger.info(f"  HTML universal generado: {os.path.basename(html_path)}")


def find_books(project_filter: str = None) -> list:
    """Busca dinámicamente carpetas de libros originales en ficcion_generada."""
    books = []
    if not os.path.exists(FICTION_DIR):
        return books
        
    for item in os.listdir(FICTION_DIR):
        full_path = os.path.join(FICTION_DIR, item)
        # Ignorar directorios de output refinados o archivos
        if not os.path.isdir(full_path) or item.endswith("_refinado"):
            continue
            
        # Filtro de proyecto
        if project_filter and project_filter.lower() not in item.lower():
            continue
            
        # Verificar si tiene capitulos
        caps = _detect_caps(full_path)
        if caps:
            books.append(full_path)
            
    return sorted(books)


def main():
    parser = argparse.ArgumentParser(description="Publicador Universal Seguro")
    parser.add_argument("--project", type=str, help="Filtra las carpetas que contengan este nombre")
    parser.add_argument("--force", action="store_true", help="Fuerza la recreación de portadas y HTML")
    args = parser.parse_args()

    books_to_process = find_books(args.project)
    
    if not books_to_process:
        logger.warning(f"No se encontraron libros originales en {FICTION_DIR}")
        return

    logger.info(f"Se encontraron {len(books_to_process)} libro(s) para publicar.")

    for book_dir_path in books_to_process:
        book_name = os.path.basename(book_dir_path)
        logger.info(f"\n{'#'*60}")
        logger.info(f"PROCESANDO PROYECTO: {book_name}")
        logger.info(f"{'#'*60}")

        logger.info("\n--- FASE 1: Verificación de Portada ---")
        fix_portada(book_dir_path, force=args.force)

        logger.info("\n--- FASE 2: Formateo y Publicación Segura ---")
        try:
            result = run_rewrite_publish(book_dir_path, force=args.force)
            logger.info(f"  Publicación completada: {result}")
        except Exception as e:
            logger.error(f"  ERROR publicando {book_name}: {e}", exc_info=True)
            continue

        logger.info("\n--- FASE 3: Re-renderizar HTML ---")
        rerender_html_refinado(book_dir_path)

        # Copiar todos los assets visuales al directorio refinado (portadas, frontispiece, mapas, etc.)
        out_dir = book_dir_path.rstrip("/\\") + "_refinado"
        if os.path.isdir(book_dir_path):
            for item in os.listdir(book_dir_path):
                if item.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
                    shutil.copy2(os.path.join(book_dir_path, item), os.path.join(out_dir, item))

    logger.info("\n=== PUBLICACIÓN UNIVERSAL FINALIZADA ===")
    logger.info("Revisa los directorios _refinado/ de cada obra.")


if __name__ == "__main__":
    main()
