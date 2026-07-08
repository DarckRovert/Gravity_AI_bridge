"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   GRAVITY AI — BookWriter Node                                               ║
║                                                                              ║
║   Integra el pipeline de escritura de libros (GravityAuthor /               ║
║   GravityFictionAuthor) en el WorkflowEngine como un nodo reutilizable.    ║
║                                                                              ║
║   NODE_TYPE: "BookWriter"                                                    ║
║                                                                              ║
║   Inputs:                                                                    ║
║     prompt       (TEXT)  — idea o tema del libro                            ║
║     title        (TEXT)  — título del libro                                 ║
║     num_chapters (INT)   — número de capítulos (default 5)                  ║
║     mode         (TEXT)  — "academic" | "fiction" | "research"              ║
║     lore_file    (TEXT)  — ruta al archivo de lore (solo para fiction)      ║
║                                                                              ║
║   Outputs:                                                                   ║
║     book_path    (TEXT)  — ruta absoluta al .md principal del libro         ║
║     epub_path    (TEXT)  — ruta absoluta al .epub (si se generó)            ║
║     cover_path   (TEXT)  — ruta absoluta a la portada .png                  ║
║     book_dir     (TEXT)  — ruta al directorio del libro                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.workflow_engine import GravityNode, registry  # noqa: E402
from core.logger import log  # noqa: E402


@registry.register
class BookWriterNode(GravityNode):
    """
    Nodo que orquesta la escritura completa de un libro (académico, ficción o investigativo)
    integrándolo en el WorkflowEngine de Gravity AI Bridge.

    Modo "academic"  → GravityAuthor (book_writer.py)
    Modo "fiction"   → GravityFictionAuthor (fiction_writer.py)
    Modo "research"  → GravityResearchAuthor (research_writer.py)
    """

    NODE_TYPE = "BookWriter"
    DESCRIPTION = "Escribe un libro completo (academic/fiction/research) y retorna las rutas de salida."

    INPUT_SCHEMA = {
        "prompt": "TEXT",
        "title": "TEXT",
        "num_chapters": "INT",
        "mode": "TEXT",
        "lore_file": "TEXT",
    }
    OUTPUT_SCHEMA = {
        "book_path": "TEXT",
        "epub_path": "TEXT",
        "cover_path": "TEXT",
        "book_dir": "TEXT",
    }

    def execute(self, inputs: dict) -> dict:
        prompt = inputs.get("prompt", self.config.get("prompt", ""))
        title = inputs.get("title", self.config.get("title", "Libro Sin Título"))
        num_chapters = int(inputs.get("num_chapters", self.config.get("num_chapters", 5)))
        mode = inputs.get("mode", self.config.get("mode", "academic")).lower()
        lore_file = inputs.get("lore_file", self.config.get("lore_file", ""))

        if not prompt:
            raise ValueError("[BookWriterNode] Se requiere un 'prompt' para generar el libro.")

        log.info(f"[BookWriterNode] Iniciando libro '{title}' | modo={mode} | capítulos={num_chapters}")

        book_path = ""

        if mode == "fiction":
            from tools.fiction_writer import GravityFictionAuthor
            author = GravityFictionAuthor(
                lore_file=lore_file if lore_file and os.path.exists(lore_file) else None
            )
            book_path = author.write_fiction_book(
                prompt=prompt,
                title=title,
                num_chapters=num_chapters,
            )
        elif mode == "research":
            from tools.research_writer import GravityResearchAuthor
            author = GravityResearchAuthor()
            book_path = author.write_research_book(
                prompt=prompt,
                title=title,
                num_chapters=num_chapters,
            )
        else:
            # Default: academic
            from tools.book_writer import GravityAuthor
            author = GravityAuthor()
            book_path = author.write_book(
                prompt=prompt,
                title=title,
                num_chapters=num_chapters,
            )

        if not book_path or not os.path.exists(book_path):
            raise RuntimeError(f"[BookWriterNode] El libro no se generó correctamente. book_path={book_path}")

        book_dir = os.path.dirname(book_path)

        # Intentar generar EPUB automáticamente
        epub_path = ""
        try:
            from tools.epub_generator import generate_epub
            epub_path = generate_epub(book_dir)
            log.info(f"[BookWriterNode] EPUB generado: {epub_path}")
        except Exception as e:
            log.warning(f"[BookWriterNode] No se pudo generar EPUB: {e}")

        # Detectar portada
        cover_path = ""
        for ext in [".png", ".jpg", ".jpeg"]:
            candidate = os.path.join(book_dir, f"cover{ext}")
            if os.path.exists(candidate):
                cover_path = candidate
                break

        log.info(f"[BookWriterNode] Libro finalizado → {book_path}")

        return {
            "book_path": book_path,
            "epub_path": epub_path,
            "cover_path": cover_path,
            "book_dir": book_dir,
        }
