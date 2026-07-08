import os
import sys
import json
import logging
import time
import re
import base64
from typing import Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core import provider_manager  # noqa: E402
from tools.web_search import WebSearch  # noqa: E402
from tools import latex_cleaner  # noqa: E402
from core import image_router  # noqa: E402
from core.chapter_qa import qa_agent
from tools.llm_utils import clean_response, atomic_write, safe_complete  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("GravityResearchAuthor")




class GravityResearchAuthor:
    """
    Motor de generación de ensayos investigativos para Gravity AI Bridge.
    Integra búsqueda web real para dotar de rigor académico a los textos,
    junto a mecanismos de auto-continuación y reintentos automáticos.
    """

    def __init__(self, output_dir="ensayos_generados"):
        self.output_dir = os.path.join(BASE_DIR, output_dir)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        self.web_search_tool = WebSearch()

    def _generate_book_cover(
        self, book_dir: str, title: str, synopsis: str
    ) -> Optional[str]:
        logger.info("Fase Visual: Diseñando concepto de portada...")
        sys_prompt = (
            "You are an expert art director and conceptual artist. Based on the following book title and synopsis, "
            "write a highly detailed, cinematic, and atmospheric prompt in ENGLISH for an AI image generator (like Midjourney or Flux). "
            "The image must be suitable for a serious, philosophical, and deep book cover. "
            "Do not include text in the image prompt, focus entirely on visual symbolism, lighting, mood, and composition. "
            "Keep the prompt concise, UNDER 50 WORDS.\n\n"
            f"Title: {title}\n"
            f"Synopsis:\n{synopsis}\n\n"
            "Return ONLY the English image prompt."
        )
        messages = [{"role": "user", "content": sys_prompt}]
        image_prompt = safe_complete(provider_manager, messages).strip()

        if not image_prompt:
            logger.warning("No se pudo generar un prompt visual válido.")
            return None

        cover_path = os.path.join(book_dir, "cover.png")
        logger.info(
            f"Fase Visual: generando portada con ImageRouter (prompt: {image_prompt[:50]}...)"
        )
        result = image_router.generate(
            prompt=image_prompt,
            output_path=cover_path,
            width=832,
            height=1216,
            title=title,
        )
        if result["success"]:
            logger.info(f"Portada generada por {result['provider']}: {result['path']}")
            return result["path"]
        logger.error(f"ImageRouter: todos los métodos fallaron: {result['error']}")
        return None

    def _generate_synopsis(self, prompt: str) -> str:
        logger.info("Fase 1: Generando Contexto Teórico y Sinopsis del Ensayo...")
        # El prompt es la directiva maestra del usuario
        sys_prompt = (
            f"INSTRUCCIÓN MAESTRA DEL USUARIO:\n{prompt}\n\n"
            "Desarrolla detalladamente la tesis principal de este libro, definiendo "
            "con rigor los conceptos clave (ej. Tulpas, Lattice, Inconsciente Colectivo). "
            "Tu respuesta establecerá el marco teórico sobre el que se estructurará todo el ensayo."
        )
        messages = [{"role": "user", "content": sys_prompt}]
        return safe_complete(provider_manager, messages)

    def _generate_outline(
        self, synopsis: str, num_chapters: int, user_prompt: str
    ) -> list:
        if num_chapters > 0:
            msg_log = f"de {num_chapters} Capítulos"
            chap_instruction = f"dividida exactamente en {num_chapters} capítulos."
        else:
            msg_log = "de longitud libre"
            chap_instruction = "dividida en la cantidad de capítulos que consideres absolutamente necesaria para abarcar exhaustivamente el tema (sin límite artificial)."

        logger.info(f"Fase 2: Generando Escaleta (Índice) {msg_log}...")
        sys_prompt = (
            f"Basándote en la siguiente directiva:\n{user_prompt}\n\nY en el siguiente contexto teórico:\n{synopsis}\n\n"
            f"Crea una escaleta analítica {chap_instruction} "
            "El JSON debe tener la estructura estricta:\n"
            '{\n  "capitulos": [\n    {"numero": 1, "titulo": "...", "resumen_eventos": "Qué se argumentará aquí en detalle"}\n  ]\n}\n\n'
            "Asegúrate de que la progresión sea lógica, yendo de la ontología teórica a la síntesis sociopolítica."
        )
        messages = [{"role": "user", "content": sys_prompt}]

        response = safe_complete(provider_manager, messages, require_json=True)
        try:
            if isinstance(response, dict):
                return response.get("capitulos", [])
            elif isinstance(response, str):
                import re

                json_match = re.search(r"\{.*\}", response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                    return data.get("capitulos", [])
                return json.loads(response).get("capitulos", [])
        except Exception as e:
            logger.error(
                f"Fallo irrecuperable al generar escaleta: {e}. Se usará una genérica."
            )
            fallback_len = num_chapters if num_chapters > 0 else 5
            return [
                {
                    "numero": i,
                    "titulo": f"Capítulo {i}",
                    "resumen_eventos": "Argumentación teórica.",
                }
                for i in range(1, fallback_len + 1)
            ]

    def _do_web_search_for_chapter(
        self, chap_title: str, chap_events: str, user_prompt: str
    ) -> str:
        logger.info(
            f"Fase 2.5: Formulando consultas de investigaci\u00f3n para: '{chap_title}'..."
        )

        # Generar 3 queries desde \u00e1ngulos distintos
        sys_prompt = (
            "Eres un asistente de investigaci\u00f3n de alto nivel. Basado en el t\u00edtulo y la descripci\u00f3n del cap\u00edtulo de un libro, "
            "genera EXACTAMENTE 3 consultas de b\u00fasqueda web independientes que cubran \u00e1ngulos distintos del tema: "
            "1) el te\u00f3rico/acad\u00e9mico, 2) el emp\u00edrico/noticioso, 3) el hist\u00f3rico/contextual.\n"
            "El objetivo es encontrar datos emp\u00edricos, teor\u00edas acad\u00e9micas o informaci\u00f3n real que respalden el argumento.\n\n"
            f"Tema General del Libro:\n{user_prompt[:500]}\n\n"
            f"T\u00edtulo del Cap\u00edtulo: {chap_title}\n"
            f"Argumento: {chap_events}\n\n"
            "Devuelve SOLO las 3 consultas, una por l\u00ednea, sin numeraci\u00f3n ni explicaciones."
        )
        messages = [{"role": "user", "content": sys_prompt}]
        queries_raw = safe_complete(provider_manager, messages).strip()
        queries = [
            q.strip().strip("\"'") for q in queries_raw.split("\n") if q.strip()
        ][:3]

        if not queries:
            queries = [f"{chap_title} {chap_events[:80]}"]

        all_results = []
        seen_urls = set()

        for query in queries:
            logger.info(f"  Buscando [{query[:60]}]...")
            try:
                result = self.web_search_tool.execute(query=query)
                if result.success:
                    all_results.append(f"**Query: {query}**\n{result.stdout}")
                    # Recuperaci\u00f3n profunda: extraer URLs del resultado y scrapear top-2
                    import re as _re

                    urls = _re.findall(r"URL: (https?://\S+)", result.stdout)
                    for url in urls[:2]:
                        if url not in seen_urls:
                            seen_urls.add(url)
                            from tools.web_search import fetch_page_text

                            page_text = fetch_page_text(url, max_chars=2000)
                            if not page_text.startswith("[fetch"):
                                all_results.append(
                                    f"  [Contenido de {url[:60]}...]\n  {page_text[:1500]}"
                                )
                else:
                    logger.warning(f"  B\u00fasqueda fall\u00f3 para: {query}")
            except Exception as e:
                logger.error(f"  Error en web search: {e}")

        if not all_results:
            return "No se encontraron resultados de b\u00fasqueda para referenciar en este cap\u00edtulo."

        combined = "\n\n".join(all_results)
        logger.info(
            f"  Investigaci\u00f3n completada: {len(queries)} queries, {len(seen_urls)} p\u00e1ginas extra\u00eddas."
        )
        return combined[:8000]  # cap para no saturar el contexto del LLM

    def _write_chapter(
        self,
        chapter_data: dict,
        synopsis: str,
        full_outline_text: str,
        accumulated_history: str,
        search_results: str,
        user_prompt: str,
    ) -> str:
        chap_num = chapter_data.get("numero", 0)
        chap_title = chapter_data.get("titulo", f"Capítulo {chap_num}")
        chap_events = chapter_data.get("resumen_eventos", "")

        logger.info(f"Fase 3: Redactando Capítulo {chap_num}: {chap_title}...")

        sys_prompt = f"""INSTRUCCIÓN MAESTRA Y TONO DEL LIBRO:
{user_prompt}

Estás escribiendo un capítulo de un libro. Redacta ÚNICAMENTE EL CAPÍTULO {chap_num} ({chap_title}).
Escribe con la profundidad, el estilo y el tono que se solicite explícitamente en la INSTRUCCIÓN MAESTRA.
Evita diálogos ficticios o narrativa novelesca a menos que el tema lo exija. Escribe extensamente (idealmente entre 1500 y 3000 palabras si es posible).

CONTEXTO GLOBAL DEL LIBRO (Marco Teórico):
{synopsis}

ESCALETA COMPLETA:
{full_outline_text}

RESUMEN DE CAPÍTULOS ANTERIORES:
{accumulated_history if accumulated_history else "Este es el primer capítulo."}

--- RESULTADOS DE INVESTIGACIÓN WEB (Usa esto para dar rigor y contexto real) ---
{search_results}
---------------------------------------------------------------------------------

INSTRUCCIONES PARA ESTE CAPÍTULO:
Desarrolla estrictamente los siguientes puntos: {chap_events}

IMPORTANTE: NO uses sintaxis de LaTeX (como $$ o bloques matemáticos especiales) para fórmulas o resaltados. Escribe todo en texto plano o Markdown estándar. Para variables matemáticas usa texto plano como T_max, Sigma_T, E_at, etc.

AHORA ESCRIBE EL CAPÍTULO (Incluye el título al inicio y usa formato Markdown):
"""
        messages = [{"role": "user", "content": sys_prompt}]

        # Auto-continuación
        max_continuations = 3
        full_chapter_text = ""

        for i in range(max_continuations):
            response = safe_complete(provider_manager, messages)

            if i > 0:
                full_chapter_text += response
            else:
                full_chapter_text = response

            stripped_end = full_chapter_text.strip()
            if stripped_end and stripped_end[-1] not in ".?!\"'*:":
                logger.warning(
                    f"Capítulo {chap_num} posiblemente truncado (parte {i+1}). Pidiendo continuación..."
                )
                messages.append({"role": "assistant", "content": response})
                messages.append(
                    {
                        "role": "user",
                        "content": "La respuesta parece haberse cortado. Continúa exactamente desde donde te quedaste, sin repetir palabras.",
                    }
                )
                time.sleep(2)
            else:
                break

        # Post-procesamiento: eliminar LaTeX residual que el LLM pudo haber generado
        cleaned = latex_cleaner.full_clean(full_chapter_text.strip())
        if cleaned != full_chapter_text.strip():
            logger.info(
                f"Capítulo {chap_num}: LaTeX residual limpiado por latex_cleaner."
            )
        return cleaned

    def _summarize_chapter(self, chapter_text: str) -> str:
        logger.info("Fase Intermedia: Extrayendo síntesis del capítulo...")
        sys_prompt = (
            "Eres un académico. Resume en 2-3 párrafos los argumentos principales e hitos lógicos "
            "establecidos en este capítulo, para que sirvan de base a los capítulos posteriores.\n\n"
            f"Capítulo:\n{chapter_text}"
        )
        messages = [{"role": "user", "content": sys_prompt}]
        return safe_complete(provider_manager, messages)

    def _generate_glossary_and_bib(self, accumulated_history: str) -> str:
        logger.info("Fase Final: Generando Glosario y Referencias...")
        sys_prompt = (
            "Basado en el resumen del libro, genera dos secciones en Markdown:\n"
            "1. '# Glosario de Términos': Define los conceptos clave usados.\n"
            "2. '# Bibliografía y Referencias': Lista libros reales, autores y teorías mencionados o afines al argumento.\n\n"
            f"Resumen del Libro:\n{accumulated_history}"
        )
        messages = [{"role": "user", "content": sys_prompt}]
        return safe_complete(provider_manager, messages)

    def _post_process_markdown(self, md_content: str) -> str:
        """Pipeline completo de limpieza: LaTeX → Unicode + normalización de tablas Markdown."""
        content = latex_cleaner.full_clean(md_content)
        # Convertir #### a negrita para compatibilidad con Google Docs
        content = re.sub(r"^#### (.*?)$", r"**\1**", content, flags=re.MULTILINE)
        return content

    def write_research_book(
        self,
        prompt: str,
        title: str = "Ensayo",
        num_chapters: int = 5, review_outline: bool = False,
        max_free_chapters: int = 20,
    ):
        logger.info(f"--- INICIANDO ENSAYO: {title} ---")
        book_dir = os.path.join(self.output_dir, title.replace(" ", "_"))
        if not os.path.exists(book_dir):
            os.makedirs(book_dir)

        progress_file = os.path.join(book_dir, "progreso.json")
        book_file = os.path.join(book_dir, f"{title.replace(' ', '_')}.md")
        html_file = os.path.join(book_dir, f"{title.replace(' ', '_')}.html")
        history_file = os.path.join(book_dir, "historial.md")

        start_chapter = 1
        accumulated_history = ""
        base_context = ""
        outline = []

        if os.path.exists(progress_file) and os.path.exists(
            os.path.join(book_dir, "2_escaleta.json")
        ):
            with open(progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                start_chapter = data.get("ultimo_capitulo", 0) + 1
            with open(
                os.path.join(book_dir, "2_escaleta.json"), "r", encoding="utf-8"
            ) as f:
                outline = json.load(f)
            with open(
                os.path.join(book_dir, "1_sinopsis.md"), "r", encoding="utf-8"
            ) as f:
                base_context = f.read()
            if os.path.exists(history_file):
                with open(history_file, "r", encoding="utf-8") as f:
                    accumulated_history = f.read()
        else:
            base_context = self._generate_synopsis(prompt)
            atomic_write(os.path.join(book_dir, "1_sinopsis.md"), base_context)

            outline = self._generate_outline(base_context, num_chapters, prompt)

            atomic_write(
                os.path.join(book_dir, "2_escaleta.json"),
                json.dumps(outline, indent=2, ensure_ascii=False),
            )
            if review_outline:
                input(f"\n[HITL] Escaleta guardada en {os.path.join(book_dir, '2_escaleta.json')}. Edite el archivo si lo desea y presione ENTER para continuar...")
                with open(os.path.join(book_dir, "2_escaleta.json"), 'r', encoding='utf-8') as f:
                    outline = json.load(f)

            initial_book = f"# {title}\n\n*Investigación generada por GravityResearchAuthor*\n\n## Índice\n"
            for c in outline:
                c_title = c.get("titulo", "")
                import urllib.parse

                anchor = "#" + urllib.parse.quote(
                    c_title.lower().replace(" ", "-").replace(":", "")
                )
                initial_book += f"{c.get('numero')}. [{c_title}]({anchor})\n"
            initial_book += "\n=== CAPITULO ===\n\n"
            atomic_write(book_file, initial_book)

            atomic_write(history_file, "")

        # Si la longitud es libre, actualizamos num_chapters al tamaño real generado (seguro para reanudaciones)
        if num_chapters <= 0:
            if len(outline) > max_free_chapters:
                logger.warning(
                    f"LLM generó {len(outline)} capítulos en modo libre. Limitando a {max_free_chapters} (max_free_chapters)."
                )
                outline = outline[:max_free_chapters]
            num_chapters = len(outline)

        cover_path = os.path.join(book_dir, "cover.png")
        if not os.path.exists(cover_path):
            self._generate_book_cover(book_dir, title, base_context)

        full_outline_text = "\n".join(
            [f"Cap {c.get('numero')}: {c.get('resumen_eventos')}" for c in outline]
        )

        for chap in outline:
            chap_num = chap.get("numero")
            if chap_num < start_chapter:
                continue

            search_results = self._do_web_search_for_chapter(
                chap.get("titulo", ""), chap.get("resumen_eventos", ""), prompt
            )
            chapter_text = self._write_chapter(
                chap,
                base_context,
                full_outline_text,
                accumulated_history,
                search_results,
                prompt,
            )

            # QA Check: Validar el capítulo antes de guardarlo
            qa_result = qa_agent.validate_chapter(chapter_text, base_context, "")
            if qa_result.get("status") == "FAIL":
                logger.warning(f"QA REJECTED Cap {chap_num}: {qa_result.get('feedback')}. Reescribiendo...")
                chapter_text = self._write_chapter(
                    chap,
                    base_context,
                    full_outline_text,
                    accumulated_history,
                    search_results,
                    prompt,
                )
            else:
                logger.info(f"QA PASSED Cap {chap_num}.")

            atomic_write(os.path.join(book_dir, f"cap_{chap_num}.md"), chapter_text)

            if chap_num < num_chapters:
                new_summary = self._summarize_chapter(chapter_text)
                accumulated_history += (
                    f"\n\n--- SÍNTESIS CAP {chap_num} ---\n{new_summary}"
                )
                atomic_write(history_file, accumulated_history)

            word_count = len(chapter_text.split())
            progress_data = {"ultimo_capitulo_completado": chap_num, "total": num_chapters}
            
            if os.path.exists(progress_file):
                try:
                    with open(progress_file, "r") as pf:
                        old_progress = json.load(pf)
                        progress_data["total_words"] = old_progress.get("total_words", 0) + word_count
                except:
                    progress_data["total_words"] = word_count
            else:
                progress_data["total_words"] = word_count

            atomic_write(
                progress_file,
                json.dumps(progress_data, indent=2),
            )
            logger.info(f"[Metrics] Capítulo {chap_num}: {word_count} palabras. Total libro: {progress_data['total_words']} palabras.")

            # BUG-06 Resuelto: Append O(1) en lugar de reconstrucción dinámica O(n^2)

            # Guardado
            atomic_append(book_file, chapter_text + "\n\n=== CAPITULO ===\n\n")

            logger.info(f"Capítulo {chap_num} finalizado y guardado.")

        if not os.path.exists(os.path.join(book_dir, "anexos.md")):
            logger.info("Fase Final: Generando Anexos...")
            anexos = self._generate_glossary_and_bib(accumulated_history)
            atomic_write(os.path.join(book_dir, "anexos.md"), anexos)

        if os.path.exists(os.path.join(book_dir, "anexos.md")):
            with open(os.path.join(book_dir, "anexos.md"), "r", encoding="utf-8") as gf:
                existing_book = ""
                with open(book_file, "r", encoding="utf-8") as f:
                    existing_book = f.read()
                atomic_write(
                    book_file, existing_book + "\n\n" + gf.read() + "\n\n=== CAPITULO ===\n\n"
                )

        try:
            import markdown

            with open(book_file, "r", encoding="utf-8") as f:
                md_content = f.read()

            # Fase de post-procesamiento anti-símbolos
            cleaned_md = self._post_process_markdown(md_content)
            atomic_write(book_file, cleaned_md)

            html_content = markdown.markdown(cleaned_md, extensions=["toc", "tables"])

            cover_path = os.path.join(book_dir, "cover.png")
            cover_html = ""
            if os.path.exists(cover_path):
                try:
                    with open(cover_path, "rb") as img_f:
                        encoded = base64.b64encode(img_f.read()).decode("utf-8")
                    cover_html = f'<div style="text-align: center; margin-bottom: 2em;"><img src="data:image/png;base64,{encoded}" style="max-width: 100%; height: auto; box-shadow: 0px 4px 15px rgba(0,0,0,0.5);" alt="Portada de {title}" /></div>\n'
                except Exception as e:
                    logger.warning(f"No se pudo incrustar la portada en Base64: {e}")

            full_html = (
                '<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n</head>\n<body>\n'
                + cover_html
                + html_content
                + "\n</body>\n</html>"
            )
            atomic_write(html_file, full_html)
            logger.info(f"HTML renderizado guardado en: {html_file}")
        except Exception as e:
            logger.error(f"No se pudo generar HTML: {e}")

        return book_file


if __name__ == "__main__":
    prompt = """Actúa como un ensayista y teórico de sistemas con una perspectiva materialista-anarquista. Escribe el esquema y los capítulos de un libro titulado 'La Física del Poder'.

Premisas:

Trata la magia, la numerología y la intención mental no como misticismo, sino como una 'tecnología de la consciencia' que interactúa con la estructura informativa de la realidad (citando el Lattice de Grinberg y el Inconsciente Colectivo de Jung).

Define las ideologías y cultos como 'Tulpas' (formas-pensamiento) diseñadas para la ingeniería social.

Analiza la existencia de una élite que, mediante el conocimiento de estas leyes, moldea el tejido social como una entidad que opera desde la invisibilidad.

Mantén un tono analítico, frío, deductivo y clínico, evitando el esoterismo tradicional y enfocándote en la causalidad y la arquitectura del poder.

Propón que la libertad humana depende de la capacidad del individuo para recuperar el control sobre su propia 'tecnología mental' antes de que sea utilizada como combustible por el sistema."""

    author = GravityResearchAuthor()
    author.write_research_book(
        prompt=prompt, title="La Física del Poder", num_chapters=5
    )
