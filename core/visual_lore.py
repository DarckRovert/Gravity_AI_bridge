import os
import json
import logging
import re
from core import provider_manager

logger = logging.getLogger("VisualLore")


def ensure_lore_book(book_dir: str, synopsis: str) -> dict:
    """
    Verifica si existe la Biblia de Personajes (lore_book.json).
    Si no existe, la genera a partir de la sinopsis usando el LLM para anclar descripciones físicas.
    """
    lore_path = os.path.join(book_dir, "lore_book.json")

    if os.path.exists(lore_path):
        try:
            with open(lore_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando lore_book.json: {e}")

    logger.info("Generando Biblia de Personajes (Visual Lore) inicial...")

    prompt = f"""Eres un Director de Arte y Diseñador de Personajes de primer nivel.
Tu tarea es leer el contexto/sinopsis de esta novela y extraer a los personajes principales y secundarios mencionados.
Para cada personaje, debes crear una descripción FÍSICA INMUTABLE altamente detallada que se usará como "Prompt" para un generador de imágenes de IA.
No te centres en su personalidad, concéntrate estrictamente en su apariencia visual.
Debe ser en INGLÉS (porque los generadores de imágenes funcionan mejor así).

Incluye detalles como:
- Edad aparente, etnia, estructura facial, color exacto de pelo y ojos.
- Ropa y estilo de vestimenta característico.
- Marcas, cicatrices, o accesorios distintivos.
- Actitud corporal típica.

Adicionalmente, define un "global_style" en INGLÉS que aplique a todas las imágenes para mantener cohesión (por ejemplo: "cinematic dark sci-fi, Unreal Engine 5 render, highly detailed, atmospheric lighting, hyperrealistic").

Devuelve ÚNICAMENTE un objeto JSON con este formato (nada de markdown, solo llaves):
{{
    "global_style": "...",
    "characters": {{
        "Nombre Personaje 1": "Description in english...",
        "Nombre Personaje 2": "Description in english..."
    }}
}}

SINOPSIS:
{synopsis[:3000]}
"""

    try:
        messages = [{"role": "user", "content": prompt}]
        # temperature=0 para máxima consistencia — los personajes NUNCA deben variar entre ejecuciones
        response = provider_manager.complete(messages, options={"temperature": 0})

        # Limpiar tags de pensamiento
        import re

        response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()

        # Limpiar posibles bloques markdown del JSON
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()

        lore_data = json.loads(response)

        # Guardar
        with open(lore_path, "w", encoding="utf-8") as f:
            json.dump(lore_data, f, indent=4, ensure_ascii=False)

        logger.info(f"Biblia de Personajes guardada en {lore_path}")
        return lore_data

    except Exception as e:
        logger.error(f"Error generando visual lore: {e}. Se creará uno vacío.")
        fallback = {
            "global_style": "cinematic, hyperrealistic, highly detailed",
            "characters": {},
        }
        with open(lore_path, "w", encoding="utf-8") as f:
            json.dump(fallback, f, indent=4)
        return fallback


def inject_lore_to_prompt(lore_data: dict, base_image_prompt: str) -> str:
    """
    Construye el prompt final priorizando la identidad visual del personaje.
    Orden: [Personaje: rasgos clave] → [escena] → [estilo global]

    Reglas:
    - El personaje va al INICIO del prompt (mayor peso en los modelos de difusión).
    - Se trunca a max 80 palabras por personaje para no superar el límite de atención.
    - Búsqueda flexible: detecta "Kaelen" aunque el lore diga "Kaelen Vance (Ego)".
    - Solo se inyecta si el nombre del personaje aparece en la escena.
    """

    character_blocks = []
    import re

    for char_name, char_desc in lore_data.get("characters", {}).items():
        # Nombres de búsqueda: nombre completo + tokens individuales > 3 chars
        search_names = [char_name] + [
            t for t in char_name.replace("(", "").replace(")", "").split() if len(t) > 3
        ]
        matched = any(n.lower() in base_image_prompt.lower() for n in search_names)

        if matched:
            # Buscar inteligentemente solo "Facial features:" y "Hair:"
            face_match = re.search(
                r"Facial features:\s*(.*?)(?=\w+:|$)", char_desc, re.IGNORECASE
            )
            hair_match = re.search(r"Hair:\s*(.*?)(?=\w+:|$)", char_desc, re.IGNORECASE)

            extracted_traits = []
            if face_match:
                extracted_traits.append(face_match.group(1).strip())
            if hair_match:
                extracted_traits.append("Hair: " + hair_match.group(1).strip())

            if extracted_traits:
                truncated = " ".join(extracted_traits)
            else:
                # Fallback: truncar a 25 palabras si no hay estructura
                words = char_desc.split()
                truncated = " ".join(words[:25])

            # Limpiar nombre
            clean_name = char_name.split("(")[0].strip()
            character_blocks.append(f"{clean_name}: {truncated}")

    # Construir el prompt: personaje principal primero, luego la escena
    if character_blocks:
        # Extraer SOLO el primer personaje para evitar "concept bleeding" en Flux
        primary_char = character_blocks[0]
        final_prompt = f"{primary_char}. Scene: {base_image_prompt}"
    else:
        final_prompt = base_image_prompt

    # Estilo global al final
    global_style = lore_data.get("global_style", "")
    if global_style:
        final_prompt = f"{final_prompt}. Style: {global_style}"

    return final_prompt


# ── Deduplicación de Biblia del Lore ─────────────────────────────────────────


def deduplicate_lore_file(lore_path: str) -> int:
    """
    Limpia un archivo de lore Markdown (ej. lore_bible.md) eliminando entradas duplicadas
    en las secciones '## Nuevas Entidades Descubiertas'.

    Estrategia:
      1. Parsea los bloques H3 (### NombreEntidad: descripcion).
      2. Mantiene solo la PRIMERA aparición de cada nombre de entidad.
      3. Reescribe el archivo en limpio.

    Args:
        lore_path: Ruta absoluta al archivo .md del lore.

    Returns:
        Número de entidades duplicadas eliminadas.
    """
    if not os.path.exists(lore_path):
        logger.warning(f"[deduplicate_lore_file] Archivo no encontrado: {lore_path}")
        return 0

    with open(lore_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Separar secciones principales (H2 o H1) del resto del archivo
    # Mantener intacto todo lo que NO sea secciones de nuevas entidades
    discovery_header = "## Nuevas Entidades Descubiertas"

    # Partir el archivo en bloques por el marcador de nuevas entidades
    parts = content.split(discovery_header)
    base_content = parts[0]  # Todo lo anterior a la primera seccion de entidades
    entity_blocks = parts[1:]  # Cada bloque posterior al marcador

    if not entity_blocks:
        logger.info("[deduplicate_lore_file] No se encontraron secciones de entidades. Nada que limpiar.")
        return 0

    # Combinar todos los bloques de entidades en uno solo
    all_entities_text = "\n".join(entity_blocks)

    # Parsear cada entrada H3 (### Nombre: descripcion...)
    h3_pattern = re.compile(r"(### [^\n]+(?:\n(?!###)[^\n]*)*)")
    all_entries = h3_pattern.findall(all_entities_text)

    seen_names: set = set()
    unique_entries: list = []
    duplicates_removed = 0

    for entry in all_entries:
        # Extraer el nombre (primera palabra tras ###)
        name_match = re.match(r"### ([^:\n]+)", entry)
        if not name_match:
            unique_entries.append(entry)
            continue
        name = name_match.group(1).strip().lower()
        if name not in seen_names:
            seen_names.add(name)
            unique_entries.append(entry)
        else:
            duplicates_removed += 1
            logger.info(f"  [deduplicate] Duplicado eliminado: '{name_match.group(1).strip()}'")

    if duplicates_removed == 0:
        logger.info("[deduplicate_lore_file] No se encontraron duplicados.")
        return 0

    # Reconstruir el archivo
    new_entities_section = (
        f"\n{discovery_header}\n" + "\n".join(unique_entries)
        if unique_entries
        else ""
    )
    new_content = base_content + new_entities_section

    with open(lore_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    logger.info(
        f"[deduplicate_lore_file] Limpieza completa. {duplicates_removed} duplicados eliminados de '{lore_path}'."
    )
    return duplicates_removed
