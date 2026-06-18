import os
import sys
import json
import logging
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core import provider_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GravityFictionAuthor")

class GravityFictionAuthor:
    """
    Motor de generación iterativa de ficción para Gravity AI Bridge.
    Maneja el lore del mundo (Biblia) y asegura la continuidad de los arcos de personajes
    a lo largo de varios libros (Temporadas).
    """
    def __init__(self, output_dir="ficcion_generada", lore_file=None):
        self.output_dir = os.path.join(BASE_DIR, output_dir)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        self.lore_file_path = lore_file
        self.lore_bible = ""
        if lore_file and os.path.exists(lore_file):
            with open(lore_file, "r", encoding="utf-8") as f:
                self.lore_bible = f.read()

    def _clean_response(self, text: str) -> str:
        """Limpia etiquetas <think> (incluso si no están cerradas) sin perder el texto real."""
        import re
        if not text:
            return ""
        # Quita todos los bloques <think> cerrados
        cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        
        # Si quedó algún <think> sin cerrar, corta todo desde ahí
        if '<think>' in cleaned:
            cleaned = re.sub(r'<think>.*', '', cleaned, flags=re.DOTALL).strip()
            
        return cleaned

    def _safe_complete(self, messages: list, max_retries=3, require_json=False) -> str:
        """Ejecuta provider_manager.complete con reintentos y corrección de JSON si es necesario."""
        import time
        import json
        import re
        
        current_messages = list(messages) # Copia superficial para poder añadir correcciones
        
        for attempt in range(max_retries):
            try:
                response = provider_manager.complete(current_messages)
                cleaned = self._clean_response(response)
                
                if not cleaned or len(cleaned) < 5:
                    logger.warning(f"Respuesta vacía o muy corta en intento {attempt+1}/{max_retries}. Reintentando...")
                    time.sleep(2)
                    continue
                
                if require_json:
                    try:
                        json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
                        if json_match:
                            json.loads(json_match.group(0))
                        else:
                            json.loads(cleaned)
                    except json.JSONDecodeError:
                        logger.warning(f"JSON inválido en intento {attempt+1}/{max_retries}. Pidiendo corrección al LLM...")
                        current_messages.append({"role": "assistant", "content": response})
                        current_messages.append({"role": "user", "content": "Tu respuesta anterior no es un JSON válido. Por favor, corrige los errores de sintaxis y devuelve ÚNICAMENTE el JSON válido."})
                        time.sleep(2)
                        continue
                        
                return cleaned
                
            except Exception as e:
                logger.error(f"Error en llamada al LLM (intento {attempt+1}/{max_retries}): {e}")
                time.sleep(2)
                
        return ""

    def _generate_synopsis(self, prompt: str) -> str:
        logger.info("Fase 1: Generando Sinopsis de Temporada / Libro...")
        sys_prompt = (
            "Eres un Showrunner de HBO y aclamado autor de novelas. "
            "Basándote en la siguiente Biblia de Universo (Lore) y la petición del usuario, "
            "desarrolla una sinopsis detallada (introducción, nudo, clímax y cliffhanger) para este libro/temporada.\n\n"
            f"--- LORE BIBLE ---\n{self.lore_bible}\n----------------\n\n"
            f"Petición del Usuario / Idea Principal: {prompt}"
        )
        messages = [{"role": "user", "content": sys_prompt}]
        return self._safe_complete(messages)

    def _generate_outline(self, synopsis: str, num_chapters: int) -> list:
        logger.info(f"Fase 2: Generando Escaleta de {num_chapters} Episodios/Capítulos...")
        sys_prompt = (
            "Eres un arquitecto narrativo. Basado en la siguiente Sinopsis y el Lore, crea una escaleta estricta "
            f"dividida exactamente en {num_chapters} capítulos. Cada capítulo debe tener un arco de tensión y terminar con gancho (cliffhanger).\n"
            "Devuelve el resultado obligatoriamente en formato JSON válido.\n"
            "El JSON debe tener la estructura:\n"
            '{\n  "capitulos": [\n    {"numero": 1, "titulo": "...", "resumen_eventos": "Qué ocurre, quién interactúa y cómo termina la tensión"}\n  ]\n}\n\n'
            f"--- LORE BIBLE ---\n{self.lore_bible}\n----------------\n\n"
            f"Sinopsis:\n{synopsis}"
        )
        messages = [{"role": "user", "content": sys_prompt}]
        response = self._safe_complete(messages, require_json=True)
        import re
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                return data.get("capitulos", [])
            return json.loads(response).get("capitulos", [])
        except Exception as e:
            logger.error(f"Fallo irrecuperable al parsear la escaleta JSON tras reintentos: {e}")
            return [{"numero": i, "titulo": f"Capítulo {i}", "resumen_eventos": "Avance de la trama"} for i in range(1, num_chapters + 1)]

    def _summarize_chapter(self, chapter_text: str) -> str:
        logger.info("Fase Intermedia: Actualizando Estado de Memoria y Resumiendo...")
        sys_prompt = (
            "Eres el supervisor de continuidad (Script Supervisor). Analiza el siguiente capítulo de ficción. "
            "Debes redactar un resumen en dos partes:\n"
            "1. RESUMEN DE LA TRAMA: Qué pasó exactamente.\n"
            "2. ESTADO DE PERSONAJES Y OBJETOS: Registra cualquier muerte, herida, cambio de bando, alianza nueva o adquisición de objetos importantes.\n"
            "Esto es crucial para que la IA no olvide detalles de continuidad en el siguiente capítulo.\n\n"
            f"Capítulo:\n{chapter_text}"
        )
        messages = [{"role": "user", "content": sys_prompt}]
        return self._safe_complete(messages)

    def _generate_glossary(self, accumulated_history: str) -> str:
        logger.info("Fase Final: Generando Glosario de Ficción...")
        sys_prompt = (
            "Eres el creador del mundo de esta novela (Worldbuilder). Basado en el siguiente resumen de continuidad de la historia, "
            "genera una sección de '# Glosario del Universo' en formato Markdown. "
            "Define de forma clara y temática los 10 a 15 términos, corporaciones, tecnologías o facciones más importantes utilizados en la trama.\n\n"
            f"Memoria de Continuidad:\n{accumulated_history}"
        )
        messages = [{"role": "user", "content": sys_prompt}]
        return self._safe_complete(messages)

    def _review_and_revise_chapter(self, chapter_text: str, lore_bible: str, accumulated_history: str) -> str:
        logger.info("Fase 3.5: Auto-Edición y Corrección de Estilo...")
        sys_prompt = (
            "Eres el Editor Jefe de la novela. Tu tarea es pulir el siguiente borrador de capítulo. "
            "Corrige cualquier diálogo acartonado, mejora el ritmo, elimina clichés y asegura la regla de 'Show, Don't Tell'. "
            "CRÍTICO: No alteres los nombres, facciones ni la continuidad. Respeta la Biblia del Lore y la Memoria de Continuidad.\n"
            "Devuelve únicamente el capítulo revisado y mejorado en formato Markdown.\n\n"
            f"--- LORE BIBLE ---\n{lore_bible}\n\n"
            f"--- MEMORIA DE CONTINUIDAD ---\n{accumulated_history}\n\n"
            f"Borrador original a corregir:\n{chapter_text}"
        )
        messages = [{"role": "user", "content": sys_prompt}]
        return self._safe_complete(messages)

    def _extract_and_update_lore(self, chapter_text: str):
        if not hasattr(self, 'lore_file_path') or not self.lore_file_path or not os.path.exists(self.lore_file_path):
            return
        logger.info("Fase 3.8: Extrayendo nuevas entidades para la Biblia del Lore...")
        sys_prompt = (
            "Eres el guardián de la continuidad. Analiza el siguiente capítulo y extrae ÚNICAMENTE personajes NUEVOS, "
            "facciones, lugares o tecnologías que hayan sido inventadas en este texto y que parezcan relevantes para el universo.\n"
            "Si no hay nada nuevo relevante, devuelve 'NADA_NUEVO'. Si hay, devuélvelos en formato Markdown (ej. '### Nombre: Descripción').\n\n"
            f"Capítulo:\n{chapter_text}"
        )
        messages = [{"role": "user", "content": sys_prompt}]
        new_lore = self._safe_complete(messages)
        
        if "NADA_NUEVO" not in new_lore.upper() and len(new_lore) > 10:
            with open(self.lore_file_path, "a", encoding="utf-8") as f:
                f.write("\n\n## Nuevas Entidades Descubiertas\n" + new_lore)
            self.lore_bible += "\n\n## Nuevas Entidades Descubiertas\n" + new_lore
            logger.info("Biblia del Lore expandida dinámicamente.")

    def _compress_history(self, accumulated_history: str) -> str:
        if len(accumulated_history) > 15000:
            logger.info("Compresión de Memoria: El historial es muy grande, resumiendo...")
            sys_prompt = (
                "Resume el siguiente historial de continuidad. Mantén ÚNICAMENTE el estado actual de los personajes principales "
                "(vivos, muertos, heridos, alianzas), objetos clave, y el hilo argumental principal activo. "
                "Hazlo extremadamente denso y omite detalles menores de capítulos viejos.\n\n"
                f"Historial actual:\n{accumulated_history}"
            )
            messages = [{"role": "user", "content": sys_prompt}]
            return self._safe_complete(messages)
        return accumulated_history

    def _write_chapter(self, chapter_data: dict, synopsis: str, full_outline_text: str, accumulated_history: str) -> str:
        chap_num = chapter_data.get("numero", 0)
        chap_title = chapter_data.get("titulo", f"Capítulo {chap_num}")
        chap_events = chapter_data.get("resumen_eventos", "")
        
        logger.info(f"Fase 3: Escribiendo Capítulo {chap_num}: {chap_title}...")

        sys_prompt = f"""Eres el escritor de una aclamada novela de ficción / guion literario. Escribe ÚNICAMENTE EL CAPÍTULO {chap_num} ({chap_title}).
No escribas el libro entero ni te confundas si la memoria de continuidad tiene una numeración de capítulos diferente (por pertenecer a un libro anterior). Estamos escribiendo un libro actual con su propia escaleta. Escribe con ritmo inmersivo, diálogos creíbles, regla de "Show, Don't Tell", descripciones sensoriales y tensión narrativa. Escribe entre 2000 y 4000 palabras si es posible.

--- LORE BIBLE (Reglas del Mundo y Personajes) ---
{self.lore_bible if self.lore_bible else "Mundo original del usuario."}

CONTEXTO DE LA TEMPORADA (Sinopsis):
{synopsis}

ESCALETA COMPLETA (Tu hoja de ruta para este libro):
{full_outline_text}

MEMORIA DE CONTINUIDAD (Resumen de la historia anterior. ¡Respeta los hechos, pero no sigas su numeración si este es un nuevo libro!):
{accumulated_history if accumulated_history else "Este es el primer capítulo o prólogo."}

INSTRUCCIONES PARA EL CAPÍTULO {chap_num} AHORA:
Debes narrar los siguientes eventos: {chap_events}

AHORA ESCRIBE EL CAPÍTULO (Incluye el título al inicio y usa formato Markdown. Que fluya como la mejor literatura moderna de ficción):
"""
        messages = [{"role": "user", "content": sys_prompt}]
        
        # Auto-continuación (Anti-Truncamiento)
        import time
        max_continuations = 3
        full_chapter_text = ""

        for i in range(max_continuations):
            response = self._safe_complete(messages)
            full_chapter_text += (" " + response) if i > 0 else response

            # Chequear si terminó abruptamente
            stripped_end = full_chapter_text.strip()
            if not stripped_end:
                logger.warning(f"Capítulo {chap_num} respuesta vacía (parte {i+1}). Reintentando...")
                time.sleep(2)
            elif len(stripped_end) < 800:
                logger.warning(f"Capítulo {chap_num} anormalmente corto ({len(stripped_end)} chars, parte {i+1}). Pidiendo continuación...")
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": "La respuesta parece haberse cortado por el límite de tokens. Continúa la redacción exactamente desde donde te quedaste, sin repetir nada anterior."})
                time.sleep(2)
            elif stripped_end[-1] not in ".?!\"'*":
                logger.warning(f"Capítulo {chap_num} posiblemente truncado (parte {i+1}). Pidiendo continuación...")
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": "La respuesta parece haberse cortado por el límite de tokens. Continúa la redacción exactamente desde donde te quedaste, sin repetir nada anterior."})
                time.sleep(2)
            else:
                break  # Terminó bien
                
        return full_chapter_text.strip()

    def write_fiction_book(self, prompt: str, title: str = "Libro 1", num_chapters: int = 5, previous_history_file: str = None):
        logger.info(f"--- INICIANDO NOVELA: {title} ---")
        return self._orchestrate_writing(title, num_chapters, lambda: self._generate_synopsis(prompt), lambda s: self._generate_outline(s, num_chapters), previous_history_file=previous_history_file)

    def _orchestrate_writing(self, title, num_chapters, phase1_callable, phase2_callable, resume=True, previous_history_file=None):
        book_dir = os.path.join(self.output_dir, title.replace(" ", "_"))
        if not os.path.exists(book_dir):
            os.makedirs(book_dir)
            
        progress_file = os.path.join(book_dir, "progreso_metadata.json")
        book_file = os.path.join(book_dir, f"{title.replace(' ', '_')}.md")
        html_file = os.path.join(book_dir, f"{title.replace(' ', '_')}.html")
        history_file = os.path.join(book_dir, "historial_continuidad.md")
        
        start_chapter = 1
        accumulated_history = ""
        
        # Heredar memoria de un libro anterior si existe
        if previous_history_file and os.path.exists(previous_history_file):
            logger.info("Heredando memoria del libro anterior...")
            with open(previous_history_file, "r", encoding="utf-8") as f:
                accumulated_history = "RESUMEN DE LIBROS ANTERIORES:\n" + f.read() + "\n\n--- INICIO DEL NUEVO LIBRO ---\n"
        
        base_context = ""
        outline = []
        
        if resume and os.path.exists(progress_file) and os.path.exists(os.path.join(book_dir, "2_escaleta.json")):
            logger.info("Recuperando estado de generación previo (Checkpoint)...")
            with open(progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                start_chapter = data.get("ultimo_capitulo_completado", 0) + 1
            with open(os.path.join(book_dir, "2_escaleta.json"), "r", encoding="utf-8") as f:
                outline = json.load(f)
            with open(os.path.join(book_dir, "1_sinopsis_base.md"), "r", encoding="utf-8") as f:
                base_context = f.read().replace("# Sinopsis de Temporada\n\n", "")
            if os.path.exists(history_file):
                with open(history_file, "r", encoding="utf-8") as f:
                    accumulated_history = f.read()
        else:
            base_context = phase1_callable()
            with open(os.path.join(book_dir, "1_sinopsis_base.md"), "w", encoding="utf-8") as f:
                f.write(f"# Sinopsis de Temporada\n\n{base_context}")
                
            outline = phase2_callable(base_context)
            outline_str = json.dumps(outline, indent=2, ensure_ascii=False)
            with open(os.path.join(book_dir, "2_escaleta.json"), "w", encoding="utf-8") as f:
                f.write(outline_str)
                
            with open(book_file, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n*Novela generada por Gravity Fiction Engine*\n\n")
                f.write("## Índice\n")
                for c in outline:
                    c_title = c.get('titulo', '')
                    import urllib.parse
                    anchor = "#" + urllib.parse.quote(c_title.lower().replace(" ", "-").replace(":", ""))
                    f.write(f"{c.get('numero')}. [{c_title}]({anchor})\n")
                f.write("\n---\n\n")
                
            with open(history_file, "w", encoding="utf-8") as f:
                f.write("")

        full_outline_text = "\n".join([f"Cap {c.get('numero')}: {c.get('resumen_eventos')}" for c in outline])
        
        for chap in outline:
            chap_num = chap.get("numero")
            if chap_num < start_chapter:
                continue
                
            chapter_text = self._write_chapter(chap, base_context, full_outline_text, accumulated_history)
            
            # Validación: capítulo vacío o muy corto = error crítico, no guardar
            if not chapter_text or len(chapter_text.strip()) < 100:
                logger.error(f"Capítulo {chap_num} generado está vacío o es demasiado corto ({len(chapter_text.strip())} chars). "
                             f"NO se actualiza el checkpoint. Reintenta la generación.")
                continue
            
            # NUEVO: Fase de Auto-Edición
            chapter_text = self._review_and_revise_chapter(chapter_text, self.lore_bible, accumulated_history)
            
            # NUEVO: Expansión Dinámica del Lore
            self._extract_and_update_lore(chapter_text)
            
            with open(os.path.join(book_dir, f"cap_{chap_num}.md"), "w", encoding="utf-8") as f:
                f.write(chapter_text)
                
            if chap_num < num_chapters:
                new_summary = self._summarize_chapter(chapter_text)
                accumulated_history += f"\n\n--- ACTUALIZACIÓN POST CAP {chap_num} ---\n{new_summary}"
                
                # Compresión de Memoria si es necesario
                accumulated_history = self._compress_history(accumulated_history)
                
                with open(history_file, "w", encoding="utf-8") as f:
                    f.write(accumulated_history)
                
            # Guardado atómico de metadata (Checkpoint completado)
            with open(progress_file, "w", encoding="utf-8") as f:
                json.dump({"ultimo_capitulo_completado": chap_num, "total": num_chapters}, f)
                
            # Reconstrucción dinámica del archivo del libro maestro para evitar duplicados en reinicios
            with open(book_file, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n*Novela generada por Gravity Fiction Engine*\n\n")
                f.write("## Índice\n")
                for c in outline:
                    c_title = c.get('titulo', '')
                    import urllib.parse
                    anchor = "#" + urllib.parse.quote(c_title.lower().replace(" ", "-").replace(":", ""))
                    f.write(f"{c.get('numero')}. [{c_title}]({anchor})\n")
                f.write("\n---\n\n")
                for i in range(1, chap_num + 1):
                    cf_path = os.path.join(book_dir, f"cap_{i}.md")
                    if os.path.exists(cf_path):
                        with open(cf_path, "r", encoding="utf-8") as cf:
                            f.write(cf.read() + "\n\n---\n\n")
                            
            logger.info(f"Capítulo {chap_num} finalizado y guardado.")

        if not os.path.exists(os.path.join(book_dir, "glosario.md")):
            logger.info("Fase Final: Generando Glosario del Universo...")
            glossary_text = self._generate_glossary(accumulated_history)
            with open(os.path.join(book_dir, "glosario.md"), "w", encoding="utf-8") as f:
                f.write(glossary_text)
                
        # Asegurarse de que el glosario esté en el archivo maestro
        if os.path.exists(os.path.join(book_dir, "glosario.md")):
            with open(os.path.join(book_dir, "glosario.md"), "r", encoding="utf-8") as gf:
                with open(book_file, "a", encoding="utf-8") as f:
                    f.write("\n\n" + gf.read() + "\n\n---\n\n")
            
        try:
            import markdown
            with open(book_file, "r", encoding="utf-8") as f:
                md_content = f.read()
            html_content = markdown.markdown(md_content, extensions=['toc'])
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"HTML renderizado guardado en: {html_file}")
        except Exception as e:
            logger.error(f"No se pudo generar HTML automático: {e}")
            
        logger.info(f"¡NOVELA FINALIZADA EXITOSAMENTE! Guardado en: {book_file}")
        return book_file

if __name__ == "__main__":
    print(" Gravity Fiction Engine CLI ".center(50, "="))
    lore_path = input("Ruta a la Biblia del Lore (opcional, presiona Enter para omitir): ").strip()
    author = GravityFictionAuthor(lore_file=lore_path if lore_path else None)
    
    prompt = input("Idea de la novela / temporada: ")
    title = input("Título del Libro: ")
    caps = int(input("Número de capítulos deseados: "))
    author.write_fiction_book(prompt=prompt, title=title, num_chapters=caps)
