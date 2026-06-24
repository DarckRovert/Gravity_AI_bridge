"""
Regenerador de Imágenes de la Trilogía (Gravity AI Bridge)
Lee los archivos .md refinados que ya contienen los tags ![Ilustración](img.png)
o <!-- FAILED_IMAGE:img.png -->, infiere el prompt original analizando el contexto,
aplica el nuevo inyector de lore, y genera las imágenes reemplazando las anteriores.
Mantiene los mismos nombres de archivo para no romper el empaquetado EPUB.
"""

import os
import sys
import re
import json
import time
import logging
import hashlib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.visual_lore import inject_lore_to_prompt  # noqa: E402
from tools.pollinations_generator import generate as poll_gen  # noqa: E402
from core import provider_manager  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("Regenerator")

NEGATIVE_PROMPT = (
    "text, watermark, signature, logo, blurry, low quality, deformed hands, "
    "extra limbs, bad anatomy, ugly, cartoon, anime, letters, words, "
    "oversaturated, overexposed"
)


def _load_lore(book_dir: str) -> dict:
    lore_path = os.path.join(book_dir, "lore_book.json")
    if not os.path.exists(lore_path):
        # Intentar en el dir sin '_refinado'
        parent = os.path.dirname(book_dir)
        base = (
            os.path.basename(book_dir).replace("_refinado", "").replace("_refined", "")
        )
        lore_path = os.path.join(parent, base, "lore_book.json")

    if os.path.exists(lore_path):
        with open(lore_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"global_style": "cinematic, hyperrealistic", "characters": {}}


def _infer_prompt_from_context(context: str, cap_title: str) -> str:
    """Usa el LLM para inferir un buen prompt de imagen puramente visual."""
    sys_prompt = f"""Eres un Director de Arte experto.
A continuación te daré un extracto de un capítulo de una novela de ciencia ficción Cyberpunk ("{cap_title}").
En el centro de este texto iba una ilustración.
Tu tarea es DEDUCIR cuál debería ser el prompt visual (en INGLÉS) para generar esa imagen.

REGLAS:
- Describe puramente lo visual: iluminación, entorno, atmósfera, acciones.
- Nombra SIEMPRE con su nombre propio a los personajes explícitos que aparecen en el extracto (ej. Kaelen, Lyra). NO uses "a man" o "a woman" si sabemos quién es.
- NUNCA describas los rasgos físicos de los personajes (ni cabello, ni rostro, ni edad, ni ropa) en tu prompt. Usa SOLO sus nombres propios. El motor visual inyectará sus rasgos automáticamente y si tú los describes, causarás aberraciones visuales.
- Mantén el prompt conciso, de 2 a 4 frases máximo.

CONTEXTO:
{context}

DEVUELVE ÚNICAMENTE EL PROMPT EN INGLÉS, sin comentarios ni explicaciones adicionales.
"""
    messages = [{"role": "user", "content": sys_prompt}]
    for _ in range(3):
        try:
            resp = provider_manager.complete(messages)
            resp = re.sub(r"<think>.*?</think>", "", resp, flags=re.DOTALL).strip()
            if resp:
                return resp
        except Exception as e:
            logger.error(f"Error inferiendo prompt: {e}")
            time.sleep(2)
    return "Cyberpunk dark neo-tokyo street scene"


def process_book(refined_dir: str):
    logger.info(
        f"\n{'='*50}\nProcesando libro: {os.path.basename(refined_dir)}\n{'='*50}"
    )
    lore_data = _load_lore(refined_dir)

    # Expresiones regulares para imágenes y fallos
    img_pattern = re.compile(r"!\[.*?\]\((img_cap_[\w_]+\.png)\)")
    failed_pattern = re.compile(r"<!-- FAILED_IMAGE:(img_cap_[\w_]+\.png) -->")

    md_files = [
        f for f in os.listdir(refined_dir) if f.startswith("cap_") and f.endswith(".md")
    ]
    md_files.sort(key=lambda x: int(re.search(r"cap_(\d+)", x).group(1)))

    for md_file in md_files:
        md_path = os.path.join(refined_dir, md_file)
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Encontrar todas las ocurrencias (exitosas o fallidas)
        matches = []
        for m in img_pattern.finditer(content):
            matches.append((m.group(1), m.start(), m.end(), "success_tag"))
        for m in failed_pattern.finditer(content):
            matches.append((m.group(1), m.start(), m.end(), "failed_tag"))

        if not matches:
            continue

        logger.info(
            f"\n[{md_file}] Encontradas {len(matches)} imágenes para regenerar."
        )

        for img_filename, start_idx, end_idx, tag_type in matches:
            logger.info(f"  → Regenerando: {img_filename}")

            # 1. Extraer contexto (1000 caracteres antes y después)
            ctx_start = max(0, start_idx - 1000)
            ctx_end = min(len(content), end_idx + 1000)
            context = (
                content[ctx_start:start_idx]
                + "\n[AQUI VA LA IMAGEN]\n"
                + content[end_idx:ctx_end]
            )

            # 2. Inferir prompt base con el LLM
            logger.info("    Infiriendo prompt visual con LLM...")
            base_prompt = _infer_prompt_from_context(context, md_file)

            # 3. Anclar semilla al personaje
            char_seed = None
            for char_name in lore_data.get("characters", {}).keys():
                search_names = [char_name] + [
                    t
                    for t in char_name.replace("(", "").replace(")", "").split()
                    if len(t) > 3
                ]
                if any(n.lower() in base_prompt.lower() for n in search_names):
                    char_seed = (
                        int(hashlib.md5(char_name.encode("utf-8")).hexdigest()[:8], 16)
                        % 2147483647
                    )
                    break

            # 4. Inyectar lore (esto aplica los 80 palabras max y pone el personaje al inicio)
            final_prompt = inject_lore_to_prompt(lore_data, base_prompt)
            logger.info(f"    Prompt final: {final_prompt[:150]}...")

            # 5. Borrar la imagen vieja si existe
            img_path = os.path.join(refined_dir, img_filename)
            if os.path.exists(img_path):
                os.remove(img_path)

            # 6. Generar con Pollinations
            for attempt in range(1, 4):
                time.sleep(5)  # Rate limit gentil
                res = poll_gen(
                    prompt=final_prompt,
                    output_path=img_path,
                    width=1024,
                    height=1024,
                    seed=char_seed,
                    enhance=False,
                    negative_prompt=NEGATIVE_PROMPT,
                )
                if res.get("success"):
                    logger.info(
                        f"    ✅ Imagen generada correctamente ({img_filename})."
                    )
                    break
                else:
                    logger.warning(
                        f"    Intento {attempt} falló. Reintentando en 8s..."
                    )
                    time.sleep(8)

            # Si era un tag fallido, hay que actualizar el Markdown para que ahora sea una imagen real
            if tag_type == "failed_tag":
                placeholder = f"<!-- FAILED_IMAGE:{img_filename} -->"
                replacement = f"![Ilustración]({img_filename})"
                content = content.replace(placeholder, replacement)
                with open(md_path, "w", encoding="utf-8") as fw:
                    fw.write(content)

    # Reempaquetar el EPUB
    logger.info(f"Re-empaquetando EPUB para {os.path.basename(refined_dir)}...")
    try:
        from tools.epub_generator import generate_epub

        generate_epub(refined_dir)
        logger.info("✅ EPUB actualizado exitosamente.")
    except Exception as e:
        logger.error(f"Error empaquetando EPUB: {e}")


if __name__ == "__main__":
    books = [
        r"f:\Gravity_AI_bridge\ficcion_generada\Cenizas_del_Leviatan_Libro_1_refinado",
        r"f:\Gravity_AI_bridge\ficcion_generada\Cenizas_del_Leviatan_Libro_2_refinado",
        r"f:\Gravity_AI_bridge\ficcion_generada\Cenizas_del_Leviatan_Libro_3_refinado",
    ]

    for b in books:
        if os.path.exists(b):
            process_book(b)
        else:
            logger.warning(f"No se encontró el directorio: {b}")

    logger.info("\n¡REGENERACIÓN TOTAL COMPLETADA!")
