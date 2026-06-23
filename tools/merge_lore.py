import os
import json
import logging
from core import provider_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LoreMerger")

def merge_lore(base_lore_path: str, new_book_dir: str):
    new_lore_path = os.path.join(new_book_dir, "lore_book.json")
    synopsis_path1 = os.path.join(new_book_dir, "1_contexto_base.md")
    synopsis_path2 = os.path.join(new_book_dir, "1_sinopsis_base.md")
    
    synopsis = ""
    if os.path.exists(synopsis_path1):
        with open(synopsis_path1, "r", encoding="utf-8") as f:
            synopsis = f.read()
    elif os.path.exists(synopsis_path2):
        with open(synopsis_path2, "r", encoding="utf-8") as f:
            synopsis = f.read()
            
    with open(base_lore_path, "r", encoding="utf-8") as f:
        base_lore = json.load(f)
        
    prompt = f"""Eres un Director de Arte de primer nivel.
Tienes esta BIBLIA DE PERSONAJES EXISTENTE de la saga (formato JSON):
{json.dumps(base_lore, indent=2)}

Ahora, lee la SINOPSIS del NUEVO LIBRO de esta misma saga:
{synopsis[:3000]}

Tu tarea es identificar si hay personajes PRINCIPALES o SECUNDARIOS en esta sinopsis que NO estén en la Biblia Existente.
Si los hay, inventa una descripción FÍSICA INMUTABLE altamente detallada en INGLÉS para ellos (Edad, etnia, cara, pelo, ropa, cicatrices).
Devuelve el JSON FINAL COMPLETO fusionado (estilo global + personajes antiguos + personajes nuevos).
NO alteres las descripciones de los personajes antiguos bajo ninguna circunstancia.
Devuelve ÚNICAMENTE el JSON válido (sin markdown, solo las llaves)."""

    try:
        messages = [{"role": "user", "content": prompt}]
        response = provider_manager.complete(messages)
        
        import re
        response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()
        if '<think>' in response:
            response = re.sub(r"<think>.*", "", response, flags=re.DOTALL).strip()
            
        prefixes_to_strip = [
            "Aquí tienes", "Aquí está", "Claro, aquí", 
            "Entendido.", "¡Por supuesto!", "A continuación"
        ]
        for prefix in prefixes_to_strip:
            if response.lower().startswith(prefix.lower()):
                lines = response.split('\n')
                while lines and (lines[0].lower().startswith(prefix.lower()) or lines[0].strip() == ""):
                    lines.pop(0)
                response = '\n'.join(lines).strip()
        
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
            
        merged_lore = json.loads(response)
        
        with open(new_lore_path, "w", encoding="utf-8") as f:
            json.dump(merged_lore, f, indent=4, ensure_ascii=False)
            
        logger.info(f"Biblia de Personajes fusionada guardada en {new_lore_path}")
        
    except Exception as e:
        logger.error(f"Error fusionando lore: {e}")

if __name__ == "__main__":
    import sys
    merge_lore(sys.argv[1], sys.argv[2])
