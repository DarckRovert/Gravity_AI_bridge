"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   GRAVITY AI — Research Refiner V1.0                                       ║
║   Refinado de obras previas generadas por GravityResearchAuthor.            ║
║                                                                            ║
║   Modos:                                                                   ║
║     polish()  → limpieza técnica sin LLM (LaTeX, HTML, portada)           ║
║     rewrite() → reescritura profunda con LLM + OSINT (3 queries/cap)      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import os
import sys
import json
import re
import logging
import time
import shutil
from typing import Optional, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools import latex_cleaner
from core import image_router
from core import provider_manager
from tools.web_search import WebSearch, fetch_page_text

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ResearchRefiner")


# ── Helpers (compartidos) ─────────────────────────────────────────────────────

def _render_html(essay_dir: str, md_content: str, html_path: str, title: str = "") -> None:
    try:
        import markdown
        html_body = markdown.markdown(md_content, extensions=["toc", "tables"])
        
        cover_img = ""
        for ext in [".png", ".jpg", ".jpeg", ".svg"]:
            if os.path.exists(os.path.join(essay_dir, f"cover{ext}")):
                cover_img = f'<img src="cover{ext}" class="cover" alt="Portada" style="display: block; max-width: 400px; margin: 0 auto 2em; border-radius: 8px; box-shadow: 0 8px 30px rgba(0,0,0,0.15);" />\n'
                break

        full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{title}</title>
<style>
  body {{ font-family: Georgia, serif; max-width: 900px; margin: 40px auto;
         padding: 0 20px; line-height: 1.9; color: #1a1a2e; background: #faf8f5; }}
  h1 {{ font-size: 2.2em; border-bottom: 3px solid #c9a96e; padding-bottom: 10px; color: #1a1a2e; }}
  h2 {{ color: #3a3a5c; font-size: 1.6em; margin-top: 2em; }}
  h3 {{ color: #5a5a7c; }}
  blockquote {{ border-left: 4px solid #c9a96e; padding-left: 1.2em; color: #555; font-style: italic; margin: 1.5em 0; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1.5em 0; }}
  th, td {{ border: 1px solid #ccc; padding: 8px 14px; text-align: left; }}
  th {{ background: #f0ece4; font-weight: bold; }}
  code {{ background: #f0ece4; padding: 2px 6px; border-radius: 3px; font-size: 0.88em; }}
  hr {{ border: none; border-top: 1px solid #c9a96e; margin: 2.5em 0; opacity: 0.5; }}
  img.cover {{ display: block; max-width: 400px; margin: 0 auto 2em; border-radius: 8px; box-shadow: 0 8px 30px rgba(0,0,0,0.15); }}
</style>
</head>
<body>
{cover_img}{html_body}
</body>
</html>"""
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(full_html)
        logger.info(f"HTML renderizado: {os.path.basename(html_path)}")
    except ImportError:
        logger.warning("markdown no instalado. Saltando render HTML.")


def _load_file(path: str) -> str:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def _save_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _detect_title(essay_dir: str) -> str:
    return os.path.basename(essay_dir).replace("_", " ")


def _detect_caps(essay_dir: str) -> List[str]:
    caps = []
    for fname in sorted(os.listdir(essay_dir)):
        if re.match(r"cap_\d+\.md$", fname):
            caps.append(os.path.join(essay_dir, fname))
    return caps


def _load_escaleta(essay_dir: str) -> List[dict]:
    esc_path = os.path.join(essay_dir, "2_escaleta.json")
    if not os.path.exists(esc_path):
        return []
    with open(esc_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get("capitulos", [])
    return data


def _assemble_essay(essay_dir: str, title: str, caps: List[str]) -> str:
    escaleta = _load_escaleta(essay_dir)
    toc_lines = []
    for c in escaleta:
        import urllib.parse
        c_title = c.get("titulo", "")
        anchor = "#" + urllib.parse.quote(c_title.lower().replace(" ", "-").replace(":", ""))
        toc_lines.append(f"{c.get('numero')}. [{c_title}]({anchor})")

    content = f"# {title}\n\n*Refinado por Gravity Research Refiner*\n\n"
    if toc_lines:
        content += "## Índice\n" + "\n".join(toc_lines) + "\n\n---\n\n"

    for cap_path in caps:
        content += _load_file(cap_path) + "\n\n---\n\n"

    for extra in ["anexos.md", "glosario.md", "bibliografia.md"]:
        extra_path = os.path.join(essay_dir, extra)
        if os.path.exists(extra_path):
            content += _load_file(extra_path) + "\n\n---\n\n"

    return content


# ── Clase principal ───────────────────────────────────────────────────────────

class ResearchRefiner:
    """
    Refinador de obras generadas por GravityResearchAuthor (ensayos OSINT).

    Uso:
        rr = ResearchRefiner()
        rr.polish("ruta/ensayos_generados/El_Cero_Operativo")
        rr.rewrite("ruta/ensayos_generados/Convergencia_Entropica", depth="expand")
    """

    def __init__(self):
        self.web_search_tool = WebSearch()

    def _clean_response(self, text: str) -> str:
        """Limpia etiquetas <think> y marcadores conversacionales."""
        import re
        if not text:
            return ""
        cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        if '<think>' in cleaned:
            cleaned = re.sub(r'<think>.*', '', cleaned, flags=re.DOTALL).strip()
            
        if cleaned.startswith("```"):
            cleaned = re.sub(r'^```[a-zA-Z0-9-]*\n', '', cleaned)
            cleaned = re.sub(r'\n```$', '', cleaned)
            
        prefixes_to_strip = [
            "Aquí tienes", "Aquí está", "Claro, aquí", 
            "Entendido.", "¡Por supuesto!", "A continuación"
        ]
        for prefix in prefixes_to_strip:
            if cleaned.lower().startswith(prefix.lower()):
                lines = cleaned.split('\n')
                while lines and (lines[0].lower().startswith(prefix.lower()) or lines[0].strip() == ""):
                    lines.pop(0)
                cleaned = '\n'.join(lines).strip()
                
        return cleaned

    # ── MODO POLISH ───────────────────────────────────────────────────────────

    def polish(self, essay_dir: str) -> str:
        """
        Retoque fino sin LLM:
        1. Limpia LaTeX de cada cap_N.md
        2. Limpia anexos/glosario si existen
        3. Re-ensambla el .md principal
        4. Re-renderiza HTML con tablas
        5. Genera portada con ImageRouter si no existe
        """
        essay_dir = os.path.abspath(essay_dir)
        if not os.path.isdir(essay_dir):
            raise FileNotFoundError(f"Carpeta no encontrada: {essay_dir}")

        title = _detect_title(essay_dir)
        caps = _detect_caps(essay_dir)
        if not caps:
            raise ValueError(f"No se encontraron cap_N.md en: {essay_dir}")

        logger.info(f"[POLISH ENSAYO] '{title}' — {len(caps)} capítulos")

        cleaned_count = 0
        for cap_path in caps:
            original = _load_file(cap_path)
            cleaned = latex_cleaner.full_clean(original)
            if cleaned != original:
                _save_file(cap_path, cleaned)
                cleaned_count += 1
                logger.info(f"  Limpiado: {os.path.basename(cap_path)}")

        logger.info(f"  {cleaned_count}/{len(caps)} capítulos tenían LaTeX residual.")

        for extra in ["anexos.md", "glosario.md", "bibliografia.md", "historial.md"]:
            extra_path = os.path.join(essay_dir, extra)
            if os.path.exists(extra_path):
                orig = _load_file(extra_path)
                cleaned = latex_cleaner.full_clean(orig)
                if cleaned != orig:
                    _save_file(extra_path, cleaned)
                    logger.info(f"  Limpiado: {extra}")

        # Re-ensamblar
        essay_safe = title.replace(" ", "_")
        essay_md_path = os.path.join(essay_dir, f"{essay_safe}.md")
        assembled = _assemble_essay(essay_dir, title, caps)
        _save_file(essay_md_path, assembled)

        # Portada
        synopsis = _load_file(os.path.join(essay_dir, "1_sinopsis.md"))
        self._ensure_cover(essay_dir, title, synopsis[:600])

        # Re-renderizar HTML
        html_path = essay_md_path.replace(".md", ".html")
        _render_html(essay_dir, assembled, html_path, title)

        logger.info(f"[POLISH COMPLETADO] {title}")
        return essay_md_path

    # ── MODO REWRITE ──────────────────────────────────────────────────────────

    def rewrite(
        self,
        essay_dir: str,
        depth: str = "full",
        output_suffix: str = "_refinado",
        start_chapter: int = 1,
        use_osint: bool = True,
    ) -> str:
        """
        Reescritura profunda con LLM + OSINT (3 queries por capítulo).

        depth="full"    → Reescritura completa con datos OSINT frescos
        depth="expand"  → Expande el texto existente con datos adicionales
        depth="enhance" → Mejora estilo y claridad académica
        use_osint=True  → Busca datos web reales para enriquecer cada cap
        """
        essay_dir = os.path.abspath(essay_dir)
        if not os.path.isdir(essay_dir):
            raise FileNotFoundError(f"Carpeta no encontrada: {essay_dir}")

        title = _detect_title(essay_dir)
        caps = _detect_caps(essay_dir)
        if not caps:
            raise ValueError(f"No se encontraron cap_N.md en: {essay_dir}")

        out_dir = essay_dir.rstrip("/\\") + output_suffix
        os.makedirs(out_dir, exist_ok=True)

        # Copiar archivos estructurales
        for fname in ["2_escaleta.json", "1_sinopsis.md", "1_contexto_base.md"]:
            src = os.path.join(essay_dir, fname)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(out_dir, fname))

        logger.info(f"[REWRITE ENSAYO/{depth.upper()}] '{title}' → {os.path.basename(out_dir)}")

        synopsis = _load_file(os.path.join(essay_dir, "1_sinopsis.md"))
        escaleta = _load_escaleta(essay_dir)
        full_outline = "\n".join(
            [f"Cap {c.get('numero')}: {c.get('titulo')} — {c.get('resumen_eventos','')[:200]}"
             for c in escaleta]
        )
        history_text = _load_file(os.path.join(essay_dir, "historial.md"))

        accumulated = ""
        progress_path = os.path.join(out_dir, "progreso.json")
        completed_until = 0
        if os.path.exists(progress_path):
            with open(progress_path) as f:
                prog = json.load(f)
            completed_until = prog.get("ultimo_capitulo", 0)

        new_caps_paths = []

        for cap_path in caps:
            cap_num = int(re.search(r"cap_(\d+)\.md", os.path.basename(cap_path)).group(1))
            if cap_num < start_chapter or cap_num <= completed_until:
                logger.info(f"  Saltando cap_{cap_num} (ya completado)")
                new_cap_path = os.path.join(out_dir, f"cap_{cap_num}.md")
                if os.path.exists(new_cap_path):
                    new_caps_paths.append(new_cap_path)
                continue

            original_text = _load_file(cap_path)
            chap_data = next((c for c in escaleta if c.get("numero") == cap_num), {})
            chap_title = chap_data.get("titulo", f"Capítulo {cap_num}")
            chap_events = chap_data.get("resumen_eventos", "")

            logger.info(f"  Reescribiendo cap_{cap_num}: {chap_title}")

            # OSINT: 3 queries independientes
            search_context = ""
            if use_osint:
                search_context = self._fetch_osint(
                    chap_title, chap_events, synopsis[:500]
                )

            new_text = self._rewrite_chapter(
                cap_num=cap_num,
                chap_title=chap_title,
                chap_events=chap_events,
                original_text=original_text,
                synopsis=synopsis,
                full_outline=full_outline,
                accumulated_history=accumulated or history_text,
                search_context=search_context,
                depth=depth,
            )

            new_cap_path = os.path.join(out_dir, f"cap_{cap_num}.md")
            _save_file(new_cap_path, new_text)
            new_caps_paths.append(new_cap_path)

            summary = self._summarize_chapter(new_text)
            accumulated += f"\n\nResumen Cap {cap_num}:\n{summary}"
            _save_file(os.path.join(out_dir, "historial.md"), accumulated)

            with open(progress_path, "w") as f:
                json.dump({"ultimo_capitulo": cap_num, "total": len(caps)}, f)

            logger.info(f"  cap_{cap_num} completado.")
            time.sleep(1)

        # Ensamblar
        new_title = f"{title} (Refinado)"
        sorted_caps = sorted(new_caps_paths, key=lambda p: int(re.search(r"cap_(\d+)", p).group(1)))
        assembled = _assemble_essay(out_dir, new_title, sorted_caps)
        essay_safe = title.replace(" ", "_")
        essay_md_path = os.path.join(out_dir, f"{essay_safe}_refinado.md")
        _save_file(essay_md_path, assembled)

        self._ensure_cover(out_dir, new_title, synopsis[:600])

        html_path = essay_md_path.replace(".md", ".html")
        _render_html(out_dir, assembled, html_path, new_title)

        logger.info(f"[REWRITE ENSAYO COMPLETADO] → {out_dir}")
        return essay_md_path

    # ── OSINT helper ──────────────────────────────────────────────────────────

    def _fetch_osint(self, chap_title: str, chap_events: str, book_context: str) -> str:
        """3 queries OSINT independientes por capítulo con recuperación profunda."""
        sys_prompt = (
            "Genera EXACTAMENTE 3 consultas de búsqueda web independientes sobre este tema de ensayo: "
            "1) perspectiva teórica/académica, 2) evidencia empírica/estadística, 3) contexto histórico/comparado.\n"
            f"Tema: {chap_title}\nArgumento: {chap_events[:300]}\n\n"
            "Devuelve SOLO las 3 consultas, una por línea, sin numeración."
        )
        try:
            q_raw = provider_manager.complete([{"role": "user", "content": sys_prompt}])
            q_raw = self._clean_response(q_raw)
            queries = [q.strip().strip('"\'') for q in q_raw.split("\n") if q.strip()][:3]
        except Exception:
            queries = [chap_title]

        results = []
        seen_urls = set()
        for query in queries:
            try:
                res = self.web_search_tool.execute(query=query)
                if res.success:
                    results.append(f"[Query: {query}]\n{res.stdout}")
                    urls = re.findall(r"URL: (https?://\S+)", res.stdout)
                    for url in urls[:2]:
                        if url not in seen_urls:
                            seen_urls.add(url)
                            page = fetch_page_text(url, max_chars=1500)
                            if not page.startswith("[fetch"):
                                results.append(f"  [Contenido: {url[:60]}]\n  {page[:1200]}")
            except Exception as e:
                logger.warning(f"  OSINT query falló: {e}")

        if not results:
            return "No se obtuvo contexto OSINT adicional."
        return "\n\n".join(results)[:7000]

    # ── LLM helpers ───────────────────────────────────────────────────────────

    def _rewrite_chapter(
        self, cap_num, chap_title, chap_events, original_text,
        synopsis, full_outline, accumulated_history, search_context, depth
    ) -> str:

        depth_instructions = {
            "full": (
                "Reescribe completamente este capítulo usando el texto original como referencia temática. "
                "Integra activamente los datos de investigación OSINT para enriquecer el argumento con evidencia real. "
                "El resultado debe ser notablemente más riguroso y fundamentado que el original."
            ),
            "expand": (
                "Expande este capítulo: mantén el texto original como base e inserta párrafos adicionales "
                "que integren los datos OSINT encontrados. El resultado debe ser al menos un 50% más extenso. "
                "Los datos nuevos deben integrarse de forma fluida, no como un apéndice separado."
            ),
            "enhance": (
                "Mejora el estilo académico de este capítulo sin alterar su estructura ni sus argumentos centrales. "
                "Donde sea apropiado, menciona brevemente datos o contexto obtenido en la investigación OSINT."
            ),
        }

        sys_prompt = f"""Eres un investigador y escritor académico de élite. Refinas el Capítulo {cap_num}: "{chap_title}".

INSTRUCCIÓN:
{depth_instructions.get(depth, depth_instructions['full'])}

SINOPSIS DEL ENSAYO:
{synopsis[:1200]}

ESCALETA COMPLETA:
{full_outline}

HISTORIAL ACUMULADO (continuidad con capítulos anteriores):
{accumulated_history[-1500:] if accumulated_history else "Primer capítulo."}

DATOS DE INVESTIGACIÓN OSINT (integra los relevantes):
{search_context[:3000] if search_context else "No disponible."}

ARGUMENTO DE ESTE CAPÍTULO:
{chap_events}

TEXTO ORIGINAL (referencia):
---
{original_text[:3500]}
---

REGLAS:
- Sin LaTeX ni $$ . Usa Unicode (Σ, →, ≈, etc.) o texto plano.
- Markdown estándar. Tablas con | col | col |.
- Incluye el título del capítulo al inicio.
- Mínimo 1500 palabras.

ESCRIBE EL CAPÍTULO REFINADO AHORA:"""

        messages = [{"role": "user", "content": sys_prompt}]
        full_text = ""
        for i in range(3):
            response = provider_manager.complete(messages)
            response = self._clean_response(response)
            full_text = full_text + response if i > 0 else response

            if full_text.strip() and full_text.strip()[-1] in ".?!\"'*:":
                break
            if i < 2:
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": "Continúa exactamente donde te quedaste."})
                time.sleep(2)

        return latex_cleaner.full_clean(full_text.strip())

    def _summarize_chapter(self, chapter_text: str) -> str:
        sys_prompt = (
            "Resume en 2-3 párrafos los argumentos e ideas clave de este capítulo "
            "para mantener coherencia en los siguientes.\n\n"
            f"Capítulo:\n{chapter_text[:3000]}"
        )
        resp = provider_manager.complete([{"role": "user", "content": sys_prompt}])
        return self._clean_response(resp)

    def _ensure_cover(self, essay_dir: str, title: str, synopsis_excerpt: str) -> Optional[str]:
        for ext in [".png", ".jpg", ".jpeg", ".svg"]:
            cover = os.path.join(essay_dir, f"cover{ext}")
            if os.path.exists(cover):
                logger.info(f"  Portada existente: cover{ext}")
                return cover

        logger.info("  Generando portada con ImageRouter...")
        prompt_text = (
            f"Cinematic academic essay cover for '{title}'. "
            f"Theme: {synopsis_excerpt[:150]}. "
            "Dark blue and gold palette, abstract philosophical symbolism, "
            "no text, dramatic composition, high quality, photorealistic concept art."
        )
        cover_path = os.path.join(essay_dir, "cover.png")
        result = image_router.generate(
            prompt=prompt_text,
            output_path=cover_path,
            width=832,
            height=1216,
            title=title,
        )
        if result["success"]:
            logger.info(f"  Portada: {result['provider']}")
            return result["path"]
        return None


# ── CLI ───────────────────────────────────────────────────────────────────────

def _cli():
    import argparse
    parser = argparse.ArgumentParser(description="Gravity Research Refiner")
    parser.add_argument("mode", choices=["polish", "rewrite"])
    parser.add_argument("path", help="Ruta a la carpeta del ensayo")
    parser.add_argument("--depth", default="full", choices=["full", "expand", "enhance"])
    parser.add_argument("--no-osint", action="store_true", help="Desactivar búsqueda OSINT")
    parser.add_argument("--from-chapter", type=int, default=1)
    args = parser.parse_args()

    rr = ResearchRefiner()
    if args.mode == "polish":
        result = rr.polish(args.path)
    else:
        result = rr.rewrite(
            args.path,
            depth=args.depth,
            start_chapter=args.from_chapter,
            use_osint=not args.no_osint,
        )
    print(f"\n✅ Completado: {result}")


if __name__ == "__main__":
    _cli()
