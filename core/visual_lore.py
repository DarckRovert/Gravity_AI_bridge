import os
import json
import logging
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
        # Usamos una temperatura baja para mayor consistencia
        response = provider_manager.complete(messages)

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
    MAX_CHAR_WORDS = 80  # límite de atención efectivo de Flux ~77 tokens

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
