import os
import sys
import json
import logging
import time
import requests
import re as _re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core import provider_manager
from tools import latex_cleaner
from core import image_router

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GravityAuthor")

class GravityAuthor:
    """
    Motor de generación iterativa de textos largos (libros) para Gravity AI Bridge.
    Maneja el límite de tokens mediante técnicas de RAG primitivo (Ventanas Deslizantes)
    y estructuración jerárquica (Sinopsis -> Escaleta -> Capítulos).
    """
    def __init__(self, output_dir="libros_generados"):
        self.output_dir = os.path.join(BASE_DIR, output_dir)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _generate_synopsis(self, prompt: str) -> str:
        logger.info("Fase 1: Generando Universo, Personajes y Sinopsis...")
        sys_prompt = (
            "Eres un aclamado autor y diseñador de mundos literarios. "
            "A partir de la idea del usuario, desarrolla una sinopsis detallada (introducción, nudo, desenlace), "
            "un perfil de los personajes principales y las reglas básicas del universo.\n\n"
            f"Idea del Usuario: {prompt}"
        )
        messages = [{"role": "user", "content": sys_prompt}]
        response = provider_manager.complete(messages)
        import re
        return re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()

    def _generate_outline(self, synopsis: str, num_chapters: int) -> list:
        logger.info(f"Fase 2: Generando Escaleta (Índice) para {num_chapters} capítulos...")
        sys_prompt = (
            "Eres un arquitecto narrativo. Basado en la siguiente Sinopsis/Mundo, crea una escaleta estricta "
            f"dividida exactamente en {num_chapters} capítulos. Devuelve el resultado obligatoriamente en formato JSON válido.\n"
            "El JSON debe tener la estructura:\n"
            '{\n  "capitulos": [\n    {"numero": 1, "titulo": "...", "resumen_eventos": "Qué ocurre exactamente aquí"}, ...\n  ]\n}\n\n'
            f"Sinopsis:\n{synopsis}"
        )
        messages = [{"role": "user", "content": sys_prompt}]
        response = provider_manager.complete(messages)
        import re
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
        try:
            if isinstance(response, dict):
                return response.get("capitulos", [])
            elif isinstance(response, str):
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                    return data.get("capitulos", [])
                return json.loads(response).get("capitulos", [])
        except Exception as e:
            logger.error(f"Fallo al parsear la escaleta JSON: {e}. Generando estructura de emergencia.")
            return [{"numero": i, "titulo": f"Capítulo {i}", "resumen_eventos": "Continuación de la historia"} for i in range(1, num_chapters + 1)]
        return []

    def _summarize_chapter(self, chapter_text: str) -> str:
        logger.info("Fase Intermedia: Resumiendo el capítulo recién generado...")
        sys_prompt = (
            "Resume detalladamente los eventos que ocurrieron en el siguiente capítulo. "
            "Menciona qué personajes hicieron qué y dónde quedaron al final, para que el próximo capítulo sepa desde dónde arrancar.\n\n"
            f"Capítulo:\n{chapter_text}"
        )
        messages = [{"role": "user", "content": sys_prompt}]
        response = provider_manager.complete(messages)
        import re
        return re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()

    def _generate_bibliography(self, accumulated_history: str) -> str:
        logger.info("Fase Final: Generando Bibliografía...")
        sys_prompt = (
            "Eres un académico experto. Basado en el siguiente resumen completo de un libro, "
            "genera una sección de '# Bibliografía y Referencias' en formato Markdown. "
            "Incluye tanto obras reales y fundamentales relevantes a los temas tratados (filosofía, política, economía) "
            "como referencias teóricas que den soporte a los argumentos. "
            "Estructúralo como un anexo final académico serio.\n\n"
            f"Resumen del Libro:\n{accumulated_history}"
        )
        messages = [{"role": "user", "content": sys_prompt}]
        response = provider_manager.complete(messages)
        import re
        return re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()

    def _generate_glossary(self, accumulated_history: str) -> str:
        logger.info("Fase Final: Generando Glosario de Términos...")
        sys_prompt = (
            "Eres un académico experto. Basado en el siguiente resumen completo de un libro, "
            "genera una sección de '# Glosario de Términos' en formato Markdown. "
            "Define de forma clara, rigurosa y académica los 10 a 15 conceptos y términos más complejos o importantes utilizados en el texto.\n\n"
            f"Resumen del Libro:\n{accumulated_history}"
        )
        messages = [{"role": "user", "content": sys_prompt}]
        response = provider_manager.complete(messages)
        import re
        return re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()

    def _write_chapter(self, chapter_data: dict, synopsis: str, full_outline_text: str, accumulated_history: str, source_text: str = None) -> str:
        chap_num = chapter_data.get("numero", 0)
        chap_title = chapter_data.get("titulo", f"Capítulo {chap_num}")
        chap_events = chapter_data.get("resumen_eventos", "")
        
        logger.info(f"Fase 3: Escribiendo Capítulo {chap_num}: {chap_title}...")
        
        expansion_instructions = ""
        if source_text:
            expansion_instructions = (
                "\nINSTRUCCIÓN ESPECIAL DE EXPANSIÓN: Estás reescribiendo y expandiendo un borrador previo. "
                "Tu objetivo es profundizar rigurosamente. Usa lenguaje académico y sólido. "
                "CRÍTICO: Si el capítulo es de Filosofía (Ej. Stirner), no hables de leyes o política práctica. "
                "Si el capítulo es Político, no hables de doctrina jurídica. "
                "Si el capítulo es Doctrinal, no mezcles filosofía ontológica. Mantén la pureza del tema asignado en la escaleta. "
                "Haz que parezca escrito por un erudito en la materia."
            )

        sys_prompt = f"""Eres el escritor de un libro. Se te pide escribir ÚNICAMENTE EL CAPÍTULO {chap_num} ({chap_title}).
No escribas el libro entero. Solo este capítulo, con detalle narrativo/argumentativo profundo. Escribe al menos 1500 a 3000 palabras si es posible.{expansion_instructions}

CONTEXTO GLOBAL DEL LIBRO (Sinopsis y Mundo / Temática):
{synopsis}

ESCALETA COMPLETA (Para que sepas dónde estás en la estructura de la obra):
{full_outline_text}

RESUMEN DE TODOS LOS CAPÍTULOS ANTERIORES (Historial acumulativo para mantener continuidad perfecta):
{accumulated_history if accumulated_history else "Este es el primer capítulo o introducción."}

INSTRUCCIONES PARA EL CAPÍTULO {chap_num} AHORA:
Debes narrar, argumentar o desarrollar lo siguiente: {chap_events}

AHORA ESCRIBE EL CAPÍTULO (Incluye el título al inicio y usa formato Markdown):
"""
        messages = [{"role": "user", "content": sys_prompt}]
        # Auto-continuación por posible truncamiento
        full_text = ""
        for _i in range(3):
            response = provider_manager.complete(messages)
            response = _re.sub(r'<think>.*?</think>', '', response, flags=_re.DOTALL).strip()
            full_text = (full_text + response) if _i > 0 else response
            if full_text.strip() and full_text.strip()[-1] in ".?!\"'*:":
                break
            if _i < 2:
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": "Continúa exactamente desde donde te quedaste."})
                time.sleep(1)
        return latex_cleaner.full_clean(full_text.strip())

    def write_book(self, prompt: str, title: str = "Mi Libro Generado", num_chapters: int = 5):
        logger.info(f"--- INICIANDO PROYECTO LITERARIO: {title} ---")
        return self._orchestrate_writing(title, num_chapters, lambda: self._generate_synopsis(prompt), lambda s: self._generate_outline(s, num_chapters))

    # --- NUEVAS FUNCIONES DE LECTURA Y EXPANSIÓN ---
    
    def _extract_text_from_google_docs(self, url: str) -> str:
        if "/edit" in url:
            url = url.split("/edit")[0] + "/export?format=txt"
        
        logger.info(f"Descargando borrador desde: {url}")
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            raise Exception("No se pudo descargar el Google Doc. Asegúrate de que el enlace sea público.")
        return r.text

    def _analyze_document(self, source_text: str) -> str:
        logger.info("Fase 1: Analizando y deconstruyendo el documento fuente...")
        sys_prompt = (
            "Eres un analista literario y académico. Analiza el siguiente borrador incompleto.\n"
            "INSTRUCCIÓN ESTRUCTURAL CRÍTICA: Debes extraer y deconstruir el texto forzosamente en TRES PILARES separados:\n"
            "1) Pilar Filosófico: Ontología del individuo. Debes INCLUIR y fundamentar todo usando a Max Stirner y su filosofía del Egoísmo ('El único y su propiedad').\n"
            "2) Pilar Político: Monopolio de la violencia, coerción del Estado y dinámica de poder.\n"
            "3) Pilar Doctrinal/Jurídico: Ley policéntrica, viabilidad de contratos y arquitectura económica descentralizada.\n"
            "No mezcles los conceptos. Cada pilar debe ser hermético.\n\n"
            f"TEXTO ORIGINAL:\n{source_text}"
        )
        messages = [{"role": "user", "content": sys_prompt}]
        response = provider_manager.complete(messages)
        import re
        return re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()

    def _generate_expansion_outline(self, analysis: str, num_chapters: int) -> list:
        logger.info(f"Fase 2: Generando Escaleta de Expansión para {num_chapters} capítulos...")
        sys_prompt = (
            "Eres un arquitecto editorial. Basado en el siguiente análisis, crea un índice de "
            f"exactamente {num_chapters} capítulos diseñados para REESCRIBIR Y EXPANDIR el borrador.\n"
            "REGLA DE ORO ESTRUCTURAL: La escaleta debe estar dividida secuencialmente. "
            "Los primeros capítulos DEBEN SER PURAMENTE FILOSÓFICOS (basados fuertemente en Max Stirner). "
            "Los siguientes capítulos DEBEN SER PURAMENTE POLÍTICOS (estructuras de poder). "
            "Los capítulos finales DEBEN SER PURAMENTE DOCTRINALES/JURÍDICOS (policentrismo, Ostrom). "
            "NO mezcles filosofía con doctrina en un mismo capítulo.\n"
            "El JSON debe tener la estructura:\n"
            '{\n  "capitulos": [\n    {"numero": 1, "titulo": "...", "resumen_eventos": "Qué se argumentará o narrará exactamente aquí..."}\n  ]\n}\n\n'
            f"Análisis del Borrador:\n{analysis}"
        )
        messages = [{"role": "user", "content": sys_prompt}]
        response = provider_manager.complete(messages)
        import re
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
        try:
            if isinstance(response, dict):
                return response.get("capitulos", [])
            elif isinstance(response, str):
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                    return data.get("capitulos", [])
                return json.loads(response).get("capitulos", [])
        except Exception as e:
            logger.error(f"Fallo al parsear la escaleta JSON: {e}")
            return [{"numero": i, "titulo": f"Capítulo {i}", "resumen_eventos": "Expansión del ensayo"} for i in range(1, num_chapters + 1)]
        return []

    def rewrite_and_expand_document(self, source_url: str, title: str = "Libro Expandido", num_chapters: int = 5):
        logger.info(f"--- INICIANDO EXPANSIÓN LITERARIA: {title} ---")
        source_text = self._extract_text_from_google_docs(source_url)
        
        return self._orchestrate_writing(
            title, 
            num_chapters, 
            lambda: self._analyze_document(source_text), 
            lambda s: self._generate_expansion_outline(s, num_chapters),
            source_text=source_text
        )

    # --- ORQUESTADOR PRINCIPAL REUTILIZABLE ---
    def _orchestrate_writing(self, title, num_chapters, phase1_callable, phase2_callable, source_text=None, resume=True):
        book_dir = os.path.join(self.output_dir, title.replace(" ", "_"))
        if not os.path.exists(book_dir):
            os.makedirs(book_dir)
            
        progress_file = os.path.join(book_dir, "progreso_metadata.json")
        book_file = os.path.join(book_dir, f"{title.replace(' ', '_')}.md")
        html_file = os.path.join(book_dir, f"{title.replace(' ', '_')}.html")
        history_file = os.path.join(book_dir, "historial_acumulado.md")
        
        start_chapter = 1
        accumulated_history = ""
        base_context = ""
        outline = []
        
        if resume and os.path.exists(progress_file) and os.path.exists(os.path.join(book_dir, "2_escaleta.json")):
            logger.info("Recuperando estado de generación previo (Checkpoint)...")
            with open(progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                start_chapter = data.get("ultimo_capitulo_completado", 0) + 1
            with open(os.path.join(book_dir, "2_escaleta.json"), "r", encoding="utf-8") as f:
                outline = json.load(f)
            with open(os.path.join(book_dir, "1_contexto_base.md"), "r", encoding="utf-8") as f:
                base_context = f.read().replace("# Contexto / Análisis\n\n", "")
            if os.path.exists(history_file):
                with open(history_file, "r", encoding="utf-8") as f:
                    accumulated_history = f.read()
        else:
            # 1. Base (Sinopsis o Análisis)
            base_context = phase1_callable()
            with open(os.path.join(book_dir, "1_contexto_base.md"), "w", encoding="utf-8") as f:
                f.write(f"# Contexto / Análisis\n\n{base_context}")
                
            # 2. Escaleta
            outline = phase2_callable(base_context)
            outline_str = json.dumps(outline, indent=2, ensure_ascii=False)
            with open(os.path.join(book_dir, "2_escaleta.json"), "w", encoding="utf-8") as f:
                f.write(outline_str)
                
            # Preparar archivo principal
            with open(book_file, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n*Generado y Expandido por Gravity AI Bridge*\n\n")
                f.write("## Índice\n")
                for c in outline:
                    c_title = c.get('titulo', '')
                    import urllib.parse
                    anchor = "#" + urllib.parse.quote(c_title.lower().replace(" ", "-").replace(":", ""))
                    f.write(f"{c.get('numero')}. [{c_title}]({anchor})\n")
                f.write("\n---\n\n")
                
            with open(history_file, "w", encoding="utf-8") as f:
                f.write("")

        # 3. Ciclo de Escritura
        full_outline_text = "\n".join([f"Cap {c.get('numero')}: {c.get('resumen_eventos')}" for c in outline])
        
        for chap in outline:
            chap_num = chap.get("numero")
            if chap_num < start_chapter:
                continue
                
            chapter_text = self._write_chapter(chap, base_context, full_outline_text, accumulated_history, source_text)
            
            with open(os.path.join(book_dir, f"cap_{chap_num}.md"), "w", encoding="utf-8") as f:
                f.write(chapter_text)
                
            with open(book_file, "a", encoding="utf-8") as f:
                f.write(chapter_text + "\n\n---\n\n")
                
            if chap_num < num_chapters:
                new_summary = self._summarize_chapter(chapter_text)
                accumulated_history += f"\n\nResumen Cap {chap_num}:\n{new_summary}"
                with open(history_file, "w", encoding="utf-8") as f:
                    f.write(accumulated_history)
                
            with open(progress_file, "w", encoding="utf-8") as f:
                json.dump({"ultimo_capitulo_completado": chap_num, "total": num_chapters}, f)
                
            logger.info(f"Capítulo {chap_num} finalizado y guardado.")
            
        # Generar Bibliografía y Glosario
        if not resume or not os.path.exists(os.path.join(book_dir, "bibliografia.md")):
            logger.info("Fase Final: Generando Bibliografía y Referencias...")
            bibliography_text = self._generate_bibliography(accumulated_history)
            glossary_text = self._generate_glossary(accumulated_history)
            with open(os.path.join(book_dir, "bibliografia.md"), "w", encoding="utf-8") as f:
                f.write(bibliography_text)
            with open(os.path.join(book_dir, "glosario.md"), "w", encoding="utf-8") as f:
                f.write(glossary_text)
            with open(book_file, "a", encoding="utf-8") as f:
                f.write("\n\n" + glossary_text + "\n\n---\n\n" + bibliography_text + "\n\n---\n\n")

        # Render HTML nativo al finalizar (con tablas)
        try:
            import markdown
            with open(book_file, "r", encoding="utf-8") as f:
                md_content = f.read()
            html_body = markdown.markdown(md_content, extensions=['toc', 'tables'])
            full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{title}</title>
<style>
  body {{ font-family: Georgia, serif; max-width: 900px; margin: 40px auto;
         padding: 0 20px; line-height: 1.8; color: #1a1a2e; background: #faf8f5; }}
  h1 {{ font-size: 2.2em; border-bottom: 3px solid #c9a96e; padding-bottom: 10px; }}
  h2 {{ color: #3a3a5c; font-size: 1.6em; margin-top: 2em; }}
  h3 {{ color: #5a5a7c; }}
  blockquote {{ border-left: 4px solid #c9a96e; padding-left: 1em; color: #555; font-style: italic; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1.5em 0; }}
  th, td {{ border: 1px solid #ccc; padding: 8px 12px; text-align: left; }}
  th {{ background: #f0ece4; font-weight: bold; }}
  hr {{ border: none; border-top: 1px solid #c9a96e; margin: 2em 0; opacity: 0.5; }}
</style>
</head>
<body>
{{html_body}}
</body>
</html>""".format(html_body=html_body)
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(full_html)
            logger.info(f"HTML renderizado guardado en: {html_file}")
        except Exception as e:
            logger.error(f"No se pudo generar HTML automático: {e}")

        # Generar portada si no existe
        cover_path = os.path.join(book_dir, "cover.png")
        if not os.path.exists(cover_path):
            try:
                synopsis_excerpt = base_context[:400] if base_context else title
                prompt_text = (
                    f"Cinematic literary book cover for '{title}'. "
                    f"Theme: {synopsis_excerpt[:200]}. "
                    "Dark atmospheric lighting, dramatic cinematic composition, "
                    "no text or letters visible, photorealistic concept art, high quality."
                )
                result = image_router.generate(
                    prompt=prompt_text, output_path=cover_path,
                    width=832, height=1216, title=title
                )
                if result["success"]:
                    logger.info(f"Portada generada vía {result['provider']}")
            except Exception as e:
                logger.warning(f"No se pudo generar portada: {e}")
            
        logger.info(f"¡LIBRO FINALIZADO EXITOSAMENTE! Guardado en: {book_file}")
        return book_file

if __name__ == "__main__":
    print(" Gravity Author Module CLI ".center(50, "="))
    
    print("1) Escribir un libro desde cero (Prompting)")
    print("2) Expandir un borrador desde Google Docs")
    opcion = input("Elige una opción (1 o 2): ")
    
    author = GravityAuthor()
    if opcion == "1":
        prompt = input("Idea del libro: ")
        title = input("Título: ")
        author.write_book(prompt=prompt, title=title, num_chapters=3)
    elif opcion == "2":
        url = input("URL de Google Docs (con permisos de lectura): ")
        title = input("Título del Libro Final: ")
        caps = int(input("Número de capítulos deseados: "))
        author.rewrite_and_expand_document(source_url=url, title=title, num_chapters=caps)
