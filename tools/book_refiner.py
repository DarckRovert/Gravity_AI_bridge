"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   GRAVITY AI — Book Refiner V1.0                                           ║
║   Refinado de obras previas generadas por GravityAuthor (book_writer.py).  ║
║                                                                            ║
║   Modos:                                                                   ║
║     polish()  → limpieza técnica sin LLM (LaTeX, HTML, portada)           ║
║     rewrite() → reescritura profunda con LLM capítulo por capítulo        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import re
import logging
import time
from typing import Optional, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools import latex_cleaner  # noqa: E402
from core import image_router  # noqa: E402
from core import provider_manager  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("BookRefiner")


# ── Helpers ───────────────────────────────────────────────────────────────────


def _render_html(
    book_dir: str, md_content: str, html_path: str, title: str = ""
) -> None:
    """Renderiza Markdown a HTML con soporte completo de tablas y ToC. Diseño neo-noir premium."""
    try:
        import markdown

        html_body = markdown.markdown(md_content, extensions=["toc", "tables"])

        cover_img = ""
        for ext in [".png", ".jpg", ".jpeg"]:
            cover_path = os.path.join(book_dir, f"cover{ext}")
            if os.path.exists(cover_path):
                cover_img = (
                    f'<div class="cover-wrapper">'
                    f'<img src="cover{ext}" class="cover" alt="Portada" />'
                    f"</div>\n"
                )
                break

        full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Lora:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg-deep: #09090f;
    --bg-card: #10101c;
    --text-main: #d8d4ee;
    --text-muted: #8a87a8;
    --accent-cyan: #00c9ff;
    --accent-glow: rgba(0, 201, 255, 0.18);
    --accent-gold: #f5c518;
    --border-subtle: rgba(0, 201, 255, 0.15);
  }}
  *, *::before, *::after {{ box-sizing: border-box; }}
  html {{ scroll-behavior: smooth; }}
  body {{
    font-family: 'Lora', Georgia, serif;
    font-size: 1.08rem;
    line-height: 1.85;
    color: var(--text-main);
    background: var(--bg-deep);
    max-width: 820px;
    margin: 0 auto;
    padding: 2rem 1.5rem 6rem;
  }}
  .cover-wrapper {{
    text-align: center;
    margin: 0 auto 3rem;
    max-width: 480px;
  }}
  .cover-wrapper img {{
    width: 100%;
    border-radius: 6px;
    box-shadow: 0 0 40px rgba(0, 201, 255, 0.25), 0 20px 60px rgba(0,0,0,0.8);
  }}
  h1 {{
    font-family: 'Rajdhani', sans-serif;
    font-size: 2.6rem;
    font-weight: 700;
    color: var(--accent-cyan);
    text-shadow: 0 0 20px rgba(0, 201, 255, 0.4);
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-top: 2.5rem;
    margin-bottom: 0.5rem;
    animation: fadein 0.8s ease-in;
  }}
  h2 {{
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.75rem;
    font-weight: 600;
    color: #7ec8e3;
    letter-spacing: 0.03em;
    margin-top: 3rem;
    margin-bottom: 1rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid var(--border-subtle);
  }}
  h3 {{
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.3rem;
    color: #a0b4cc;
    margin-top: 2rem;
  }}
  p {{ margin: 0 0 1.2rem; }}
  em {{ color: #c0bade; font-style: italic; }}
  strong {{ color: #eae7ff; }}
  blockquote {{
    margin: 1.5rem 0;
    padding: 1rem 1.4rem;
    border-left: 3px solid var(--accent-cyan);
    background: var(--accent-glow);
    color: #c8c4e0;
    font-style: italic;
    border-radius: 0 4px 4px 0;
  }}
  hr {{
    border: none;
    height: 1px;
    background: linear-gradient(to right, transparent, var(--accent-cyan), transparent);
    box-shadow: 0 0 8px rgba(0, 201, 255, 0.4);
    margin: 3rem auto;
    max-width: 600px;
  }}
  code {{
    background: rgba(0, 201, 255, 0.08);
    color: var(--accent-cyan);
    padding: 2px 7px;
    border-radius: 3px;
    font-size: 0.88em;
    font-family: 'Courier New', monospace;
    border: 1px solid var(--border-subtle);
  }}
  table {{
    border-collapse: collapse;
    width: 100%;
    margin: 1.5rem 0;
    font-size: 0.94rem;
  }}
  th, td {{
    border: 1px solid var(--border-subtle);
    padding: 9px 14px;
    text-align: left;
  }}
  th {{
    background: rgba(0, 201, 255, 0.07);
    color: var(--accent-cyan);
    font-family: 'Rajdhani', sans-serif;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    font-size: 0.85rem;
  }}
  img {{
    max-width: 100%;
    height: auto;
    border-radius: 4px;
    box-shadow: 0 0 20px rgba(0, 201, 255, 0.2), 0 8px 30px rgba(0,0,0,0.6);
    display: block;
    margin: 1.5rem auto;
  }}
  a {{ color: var(--accent-cyan); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  @keyframes fadein {{
    from {{ opacity: 0; transform: translateY(-8px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
  }}
  @media (max-width: 600px) {{
    body {{ font-size: 1rem; padding: 1rem; }}
    h1 {{ font-size: 2rem; }}
    h2 {{ font-size: 1.4rem; }}
  }}
</style>
</head>
<body>
{cover_img}{html_body}
</body>
</html>"""
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(full_html)
        logger.info(f"HTML neo-noir renderizado: {os.path.basename(html_path)}")
    except ImportError:
        logger.warning("markdown no instalado. Saltando render HTML.")


def _load_escaleta(book_dir: str) -> List[dict]:
    esc_path = os.path.join(book_dir, "2_escaleta.json")
    if not os.path.exists(esc_path):
        return []
    with open(esc_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # book_writer usa {"capitulos": [...]} o lista directa
    if isinstance(data, dict):
        return data.get("capitulos", [])
    return data


def _load_file(path: str) -> str:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def _save_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _detect_title(book_dir: str) -> str:
    """Detecta el título del libro desde el nombre de la carpeta."""
    return os.path.basename(book_dir).replace("_", " ")


def _detect_caps(book_dir: str) -> List[str]:
    """Retorna lista ordenada de rutas cap_N.md existentes."""
    caps = []
    for fname in sorted(os.listdir(book_dir)):
        if re.match(r"cap_\d+\.md$", fname):
            caps.append(os.path.join(book_dir, fname))
    return caps


def _assemble_book(book_dir: str, title: str, caps: List[str]) -> str:
    """Ensambla todos los capítulos en el archivo .md principal."""
    escaleta = _load_escaleta(book_dir)
    toc_lines = []
    for c in escaleta:
        import urllib.parse

        c_title = c.get("titulo", "")
        anchor = "#" + urllib.parse.quote(
            c_title.lower().replace(" ", "-").replace(":", "")
        )
        toc_lines.append(f"{c.get('numero')}. [{c_title}]({anchor})")

    content = f"# {title}\n\n*Refinado por Gravity Book Refiner*\n\n"
    if toc_lines:
        content += "## Índice\n" + "\n".join(toc_lines) + "\n\n---\n\n"

    for cap_path in caps:
        content += _load_file(cap_path) + "\n\n---\n\n"

    # Apéndices opcionales
    for extra in ["glosario.md", "bibliografia.md"]:
        extra_path = os.path.join(book_dir, extra)
        if os.path.exists(extra_path):
            content += _load_file(extra_path) + "\n\n---\n\n"

    return content


# ── Clase principal ───────────────────────────────────────────────────────────


class BookRefiner:
    """
    Refinador de obras generadas por GravityAuthor (libros y ficción).

    Uso:
        r = BookRefiner()
        r.polish("ruta/a/La_Voluntad_Soberana")       # limpieza técnica
        r.rewrite("ruta/a/Cenizas_del_Leviatan_L1")   # reescritura con LLM
    """

    def __init__(self):
        pass

    def _clean_response(self, text: str) -> str:
        """Limpia etiquetas <think> y marcadores conversacionales."""
        import re

        if not text:
            return ""
        cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        if "<think>" in cleaned:
            cleaned = re.sub(r"<think>.*", "", cleaned, flags=re.DOTALL).strip()

        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z0-9-]*\n", "", cleaned)
            cleaned = re.sub(r"\n```$", "", cleaned)

        prefixes_to_strip = [
            "Aquí tienes",
            "Aquí está",
            "Claro, aquí",
            "Entendido.",
            "¡Por supuesto!",
            "A continuación",
        ]
        for prefix in prefixes_to_strip:
            if cleaned.lower().startswith(prefix.lower()):
                lines = cleaned.split("\n")
                while lines and (
                    lines[0].lower().startswith(prefix.lower())
                    or lines[0].strip() == ""
                ):
                    lines.pop(0)
                cleaned = "\n".join(lines).strip()

        return cleaned

    # ── MODO POLISH ───────────────────────────────────────────────────────────

    def polish(self, book_dir: str) -> str:
        """
        Retoque fino sin LLM:
        1. Aplica latex_cleaner a cada cap_N.md (in-place)
        2. Re-ensambla el .md principal
        3. Re-renderiza HTML con tablas
        4. Genera portada con ImageRouter si no existe
        Retorna: ruta al .md refinado
        """
        book_dir = os.path.abspath(book_dir)
        if not os.path.isdir(book_dir):
            raise FileNotFoundError(f"Carpeta no encontrada: {book_dir}")

        title = _detect_title(book_dir)
        caps = _detect_caps(book_dir)
        if not caps:
            raise ValueError(f"No se encontraron cap_N.md en: {book_dir}")

        logger.info(f"[POLISH] '{title}' — {len(caps)} capítulos")

        # 1. Limpiar cada capítulo
        cleaned_count = 0
        for cap_path in caps:
            original = _load_file(cap_path)
            cleaned = latex_cleaner.full_clean(original)
            if cleaned != original:
                _save_file(cap_path, cleaned)
                cleaned_count += 1
                logger.info(f"  Limpiado: {os.path.basename(cap_path)}")

        logger.info(f"  {cleaned_count}/{len(caps)} capítulos tenían LaTeX residual.")

        # 2. Limpiar apéndices (glosario, bibliografía)
        for extra in ["glosario.md", "bibliografia.md", "anexos.md"]:
            extra_path = os.path.join(book_dir, extra)
            if os.path.exists(extra_path):
                orig = _load_file(extra_path)
                cleaned = latex_cleaner.full_clean(orig)
                if cleaned != orig:
                    _save_file(extra_path, cleaned)
                    logger.info(f"  Limpiado: {extra}")

        # 3. Re-ensamblar .md principal
        book_md_path = os.path.join(book_dir, f"{title.replace(' ', '_')}.md")
        assembled = _assemble_book(book_dir, title, caps)
        _save_file(book_md_path, assembled)
        logger.info(f"  Ensamblado: {os.path.basename(book_md_path)}")

        # 4. Generar portada si no existe
        self._ensure_cover(book_dir, title, assembled[:800])

        # 5. Re-renderizar HTML
        html_path = book_md_path.replace(".md", ".html")
        _render_html(book_dir, assembled, html_path, title)

        logger.info(f"[POLISH COMPLETADO] {title}")
        return book_md_path

    # ── MODO REWRITE ──────────────────────────────────────────────────────────

    def rewrite(
        self,
        book_dir: str,
        depth: str = "full",  # "full" | "expand" | "enhance"
        output_suffix: str = "_refinado",
        start_chapter: int = 1,
    ) -> str:
        """
        Reescritura profunda con LLM capítulo por capítulo.

        depth="full"    → Reescribe completamente usando el original como referencia
        depth="expand"  → Expande el texto existente (agrega 30-50% más contenido)
        depth="enhance" → Mejora el estilo sin cambiar la estructura

        Guarda en una carpeta nueva: {titulo}_refinado/
        Retorna: ruta al .md refinado
        """
        book_dir = os.path.abspath(book_dir)
        if not os.path.isdir(book_dir):
            raise FileNotFoundError(f"Carpeta no encontrada: {book_dir}")

        title = _detect_title(book_dir)
        caps = _detect_caps(book_dir)
        if not caps:
            raise ValueError(f"No se encontraron cap_N.md en: {book_dir}")

        # Carpeta de salida
        out_dir = book_dir.rstrip("/\\") + output_suffix
        os.makedirs(out_dir, exist_ok=True)

        # Copiar archivos estructurales
        for fname in [
            "2_escaleta.json",
            "1_contexto_base.md",
            "1_sinopsis_base.md",
            "historial_acumulado.md",
            "historial_continuidad.md",
        ]:
            src = os.path.join(book_dir, fname)
            if os.path.exists(src):
                import shutil

                shutil.copy2(src, os.path.join(out_dir, fname))

        logger.info(
            f"[REWRITE/{depth.upper()}] '{title}' — {len(caps)} capítulos → {os.path.basename(out_dir)}"
        )

        # Heredar lore_book.json del libro original al out_dir
        lore_src = os.path.join(book_dir, "lore_book.json")
        lore_dst = os.path.join(out_dir, "lore_book.json")
        if os.path.exists(lore_src) and not os.path.exists(lore_dst):
            import shutil as _shutil

            _shutil.copy2(lore_src, lore_dst)
            logger.info("  lore_book.json heredado del libro original.")

        # Cargar contexto
        synopsis = (
            _load_file(os.path.join(book_dir, "1_contexto_base.md"))
            or _load_file(os.path.join(book_dir, "1_sinopsis_base.md"))
            or ""
        )

        # Generar o cargar Biblia de Personajes
        from core.visual_lore import ensure_lore_book

        lore_data = ensure_lore_book(book_dir, synopsis)
        escaleta = _load_escaleta(book_dir)
        full_outline = "\n".join(
            [
                f"Cap {c.get('numero')}: {c.get('titulo')} — {c.get('resumen_eventos','')[:200]}"
                for c in escaleta
            ]
        )

        # Cargar historial acumulado
        history_text = (
            _load_file(os.path.join(book_dir, "historial_acumulado.md"))
            or _load_file(os.path.join(book_dir, "historial_continuidad.md"))
            or ""
        )

        new_caps = []
        accumulated = ""
        progress_path = os.path.join(out_dir, "progreso_metadata.json")

        # Soporte de reanudación
        completed_until = 0
        if os.path.exists(progress_path):
            with open(progress_path, "r", encoding="utf-8") as f:
                prog = json.load(f)
                completed_until = prog.get("ultimo_capitulo_completado", 0)
            # Cargar caps ya reescritos
            for cap_path in _detect_caps(out_dir):
                new_caps.append(cap_path)

        for cap_path in caps:
            cap_num = int(
                re.search(r"cap_(\d+)\.md", os.path.basename(cap_path)).group(1)
            )
            if cap_num < start_chapter or cap_num <= completed_until:
                logger.info(
                    f"  Saltando cap_{cap_num} (ya completado o fuera de rango)"
                )
                continue

            original_text = _load_file(cap_path)
            chap_data = next((c for c in escaleta if c.get("numero") == cap_num), {})
            chap_title = chap_data.get("titulo", f"Capítulo {cap_num}")
            chap_events = chap_data.get("resumen_eventos", "")

            logger.info(f"  Procesando cap_{cap_num}: {chap_title} (Modo: {depth})")

            if depth == "publish":
                new_text = original_text
            else:
                new_text = self._rewrite_chapter(
                    cap_num=cap_num,
                    chap_title=chap_title,
                    chap_events=chap_events,
                    original_text=original_text,
                    synopsis=synopsis,
                    full_outline=full_outline,
                    accumulated_history=accumulated or history_text,
                    depth=depth,
                    lore_data=lore_data,
                    book_dir=out_dir,
                )

            # Guardar capítulo reescrito
            new_cap_path = os.path.join(out_dir, f"cap_{cap_num}.md")
            _save_file(new_cap_path, new_text)
            new_caps.append(new_cap_path)

            # Actualizar historial acumulado para continuidad
            summary = self._summarize_chapter(new_text)
            accumulated += f"\n\nResumen Cap {cap_num}:\n{summary}"
            _save_file(os.path.join(out_dir, "historial_acumulado.md"), accumulated)

            # Guardar progreso
            with open(progress_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"ultimo_capitulo_completado": cap_num, "total": len(caps)}, f
                )

            logger.info(f"  cap_{cap_num} reescrito y guardado.")
            time.sleep(1)  # rate limiting cortés

        # Ensamblar resultado final
        new_title = f"{title} (Refinado)"
        assembled = _assemble_book(
            out_dir,
            new_title,
            sorted(
                _detect_caps(out_dir),
                key=lambda p: int(re.search(r"cap_(\d+)", p).group(1)),
            ),
        )
        book_md_path = os.path.join(out_dir, f"{title.replace(' ', '_')}_refinado.md")
        _save_file(book_md_path, assembled)

        # Portada
        self._ensure_cover(out_dir, new_title, synopsis[:600])

        html_path = book_md_path.replace(".md", ".html")
        _render_html(out_dir, assembled, html_path, new_title)

        logger.info(f"[REWRITE COMPLETADO] → {out_dir}")
        return book_md_path

    # ── LLM helpers ───────────────────────────────────────────────────────────

    def _rewrite_chapter(
        self,
        cap_num: int,
        chap_title: str,
        chap_events: str,
        original_text: str,
        synopsis: str,
        full_outline: str,
        accumulated_history: str,
        depth: str,
        lore_data: Optional[dict] = None,
        book_dir: Optional[str] = None,
    ) -> str:

        depth_instructions = {
            "full": (
                "Reescribe completamente este capítulo usando el texto original como referencia temática. "
                "Mejora el estilo, la densidad argumentativa y la cohesión narrativa. "
                "Puedes cambiar la estructura de párrafos, añadir ejemplos, profundizar argumentos. "
                "El resultado debe ser notablemente superior al original."
            ),
            "expand": (
                "Expande este capítulo: manteniendo el texto original como base, "
                "inserta nuevos párrafos que profundicen los argumentos existentes, "
                "añade ejemplos concretos, citas implícitas o desarrollos adicionales. "
                "El resultado debe ser al menos un 40% más extenso que el original."
            ),
            "enhance": (
                "Mejora el estilo literario y académico de este capítulo sin alterar su contenido. "
                "Elimina repeticiones, mejora la transición entre párrafos, "
                "enriquece el vocabulario y asegura una voz coherente y elevada. "
                "Mantén exactamente la misma estructura y los mismos puntos argumentales."
            ),
        }

        instruction = depth_instructions.get(depth, depth_instructions["full"])

        sys_prompt = f"""Eres un escritor y académico de alto nivel. Se te encarga el refinado del Capítulo {cap_num}: "{chap_title}".

INSTRUCCIÓN DE REFINADO:
{instruction}

CONTEXTO GLOBAL (Sinopsis/Universo de la obra):
{synopsis[:2000]}

ESCALETA COMPLETA (estructura de la obra):
{full_outline}

HISTORIAL DE CAPÍTULOS ANTERIORES (para mantener continuidad perfecta):
{accumulated_history[-4000:] if accumulated_history else "Este es el primer capítulo."}

ARGUMENTO DE ESTE CAPÍTULO:
{chap_events}

TEXTO ORIGINAL (usa esto como referencia — respeta todos los nombres de personajes, eventos y objetos):
---
{original_text[:8000]}
---

IMPORTANTE:
- NO uses LaTeX ni fórmulas matemáticas en notación $$. Usa texto plano o Unicode.
- Escribe en Markdown estándar. Para tablas usa | col | col |.
- Incluye el título del capítulo al inicio con formato # o ##.
- Mínimo 1500 palabras. Máximo: tan largo como sea necesario para ser excelente.

AHORA ESCRIBE EL CAPÍTULO REFINADO:"""

        messages = [{"role": "user", "content": sys_prompt}]

        # Auto-continuación por si se corta
        max_cont = 3
        full_text = ""
        for i in range(max_cont):
            response = provider_manager.complete(messages)
            # Limpiar tags de pensamiento y basura conversacional
            response = self._clean_response(response)

            if i > 0:
                full_text += response
            else:
                full_text = response

            stripped = full_text.strip()
            if stripped and stripped[-1] in ".?!\"'*:":
                break
            if i < max_cont - 1:
                logger.warning(f"  cap_{cap_num} posiblemente truncado. Continuando...")
                messages.append({"role": "assistant", "content": response})
                messages.append(
                    {
                        "role": "user",
                        "content": "Continúa exactamente desde donde te quedaste, sin repetir nada.",
                    }
                )
                time.sleep(2)

        cleaned_text = latex_cleaner.full_clean(full_text.strip())

        # Procesamiento de imágenes en línea desactivado permanentemente para evitar glitches visuales.
        if False:  # lore_data and book_dir:
            # from core.visual_lore import inject_lore_to_prompt
            from tools.pollinations_generator import generate as poll_gen
            import uuid

            # Archivo de recuperación de imágenes fallidas (genérico por libro)
            failed_log_path = os.path.join(book_dir, "failed_images.json")
            try:
                with open(failed_log_path, "r", encoding="utf-8") as _f:
                    _failed_log = json.load(_f)
            except Exception:
                _failed_log = []

            # Negative prompt estándar para ficción visual (evita texto en pantalla, marcas, distorsiones)
            NEGATIVE_PROMPT = (
                "text, watermark, signature, logo, blurry, low quality, deformed hands, "
                "extra limbs, bad anatomy, ugly, cartoon, anime, letters, words, "
                "oversaturated, overexposed"
            )

            def image_replacer(match):
                base_prompt = match.group(1).strip()
                final_prompt = inject_lore_to_prompt(lore_data, base_prompt)  # noqa: F821

                img_id = uuid.uuid4().hex[:8]
                img_filename = f"img_cap_{cap_num}_{img_id}.png"
                img_path = os.path.join(book_dir, img_filename)

                # Anclar la semilla al primer personaje mencionado para coherencia facial entre escenas
                char_seed = None
                for char_name in lore_data.get("characters", {}).keys():
                    search_names = [char_name] + [
                        t
                        for t in char_name.replace("(", "").replace(")", "").split()
                        if len(t) > 3
                    ]
                    if any(n.lower() in base_prompt.lower() for n in search_names):
                        import hashlib as _hl

                        char_seed = (
                            int(_hl.md5(char_name.encode("utf-8")).hexdigest()[:8], 16)
                            % 2147483647
                        )
                        break

                logger.info(f"    Generando imagen para cap_{cap_num}: {img_filename}")
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
                    return f"\n\n![Ilustración]({img_filename})\n\n"
                else:
                    logger.warning(f"    Fallo al generar {img_filename}.")
                    # Persiste el prompt fallido para el script de reintento
                    _failed_log.append(
                        {
                            "cap_num": cap_num,
                            "img_filename": img_filename,
                            "img_path": img_path,
                            "base_prompt": base_prompt,
                            "final_prompt": final_prompt,
                            "char_seed": char_seed,
                        }
                    )
                    with open(failed_log_path, "w", encoding="utf-8") as _fw:
                        json.dump(_failed_log, _fw, indent=2, ensure_ascii=False)
                    # Retorna un placeholder en el MD para que retry_failed_images.py lo ubique
                    return f"\n\n<!-- FAILED_IMAGE:{img_filename} -->\n\n"

            cleaned_text = re.sub(
                r"<IMAGE_PROMPT>(.*?)</IMAGE_PROMPT>",
                image_replacer,
                cleaned_text,
                flags=re.DOTALL,
            )

        return cleaned_text

    def _summarize_chapter(self, chapter_text: str) -> str:
        sys_prompt = (
            "Eres el supervisor de continuidad (Script Supervisor). Resume los eventos principales de este capítulo "
            "en 3-4 párrafos detallados. Incluye: estado físico de cada personaje al final del capítulo, "
            "objetos clave adquiridos o perdidos, cambios de alianza, y el cliffhanger final si existe.\n\n"
            f"Capítulo completo:\n{chapter_text}"
        )
        messages = [{"role": "user", "content": sys_prompt}]
        resp = provider_manager.complete(messages)
        return self._clean_response(resp)

    def _ensure_cover(
        self, book_dir: str, title: str, synopsis_excerpt: str
    ) -> Optional[str]:
        """Genera portada vía ImageRouter si no existe ninguna imagen de portada."""
        for ext in [".png", ".jpg", ".jpeg", ".svg"]:
            cover_path = os.path.join(book_dir, f"cover{ext}")
            if os.path.exists(cover_path):
                logger.info(f"  Portada existente encontrada: cover{ext}")
                return cover_path

        logger.info("  Generando portada con ImageRouter...")
        # Prompt visual en inglés
        prompt_text = (
            f"Cinematic book cover for a philosophical literary work titled '{title}'. "
            f"Theme: {synopsis_excerpt[:200]}. "
            "Dark atmospheric lighting, dramatic composition, no text, no letters, "
            "photorealistic, conceptual art style, high contrast, deep shadows."
        )
        cover_path = os.path.join(book_dir, "cover.png")
        result = image_router.generate(
            prompt=prompt_text,
            output_path=cover_path,
            width=832,
            height=1216,
            title=title,
        )
        if result["success"]:
            logger.info(f"  Portada generada: {result['provider']}")
            return result["path"]
        logger.warning(f"  No se pudo generar portada: {result['error']}")
        return None


# ── CLI ───────────────────────────────────────────────────────────────────────


def _cli():
    import argparse

    parser = argparse.ArgumentParser(description="Gravity Book Refiner")
    parser.add_argument("mode", choices=["polish", "rewrite"], help="Modo de refinado")
    parser.add_argument("path", help="Ruta a la carpeta de la obra")
    parser.add_argument(
        "--depth",
        default="full",
        choices=["full", "expand", "enhance"],
        help="Profundidad del rewrite (solo en modo rewrite)",
    )
    parser.add_argument("--from-chapter", type=int, default=1, help="Capítulo inicial")
    args = parser.parse_args()

    r = BookRefiner()
    if args.mode == "polish":
        result = r.polish(args.path)
    else:
        result = r.rewrite(args.path, depth=args.depth, start_chapter=args.from_chapter)
    print(f"\n✅ Completado: {result}")


if __name__ == "__main__":
    _cli()
