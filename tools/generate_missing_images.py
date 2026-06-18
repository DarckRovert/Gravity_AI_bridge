import os
import hashlib
import json
import logging
from tools.regenerate_all_images import _infer_prompt_from_context, _load_lore, NEGATIVE_PROMPT
from core.visual_lore import inject_lore_to_prompt
from tools.pollinations_generator import generate as poll_gen

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("MissingImages")

def generate_missing(book_dir: str, cap_num: int):
    base_name = os.path.basename(book_dir)
    md_file = os.path.join(book_dir, f"cap_{cap_num}.md")
    def_dir = f"ficcion_generada/{base_name}_definitivo"
    
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    context = content[:3000]
    lore_data = _load_lore(book_dir)
    
    logger.info(f"Generando imagen faltante para {base_name} Capítulo {cap_num}")
    
    # Infiere prompt
    base_prompt = _infer_prompt_from_context(context, f"Capítulo {cap_num}")
    logger.info(f"Prompt base inferido: {base_prompt}")
    
    # Inyectar lore
    final_prompt = inject_lore_to_prompt(lore_data, base_prompt)
    logger.info(f"Prompt final (lore inyectado): {final_prompt}")
    
    # Generar un hash unico
    hash_str = hashlib.md5(final_prompt.encode("utf-8")).hexdigest()[:8]
    img_name = f"img_cap_{cap_num}_{hash_str}.png"
    img_path = os.path.join(def_dir, img_name)
    
    # Seed
    seed_hash = int(hashlib.md5(f"{base_name}_cap_{cap_num}".encode("utf-8")).hexdigest(), 16)
    seed = seed_hash % (2**32 - 1)
    
    # Generar imagen
    success = poll_gen(
        prompt=final_prompt,
        output_path=img_path,
        width=1024,
        height=1024,
        seed=seed,
        nologo=True,
        negative_prompt=NEGATIVE_PROMPT
    )
    
    if success:
        logger.info(f"Imagen generada exitosamente en {img_path}")
    else:
        logger.error("Error al generar la imagen faltante")

if __name__ == "__main__":
    generate_missing("ficcion_generada/Cenizas_del_Leviatan_Libro_1", 2)
    generate_missing("ficcion_generada/Cenizas_del_Leviatan_Libro_1", 6)
    generate_missing("ficcion_generada/Cenizas_del_Leviatan_Libro_2", 5)
