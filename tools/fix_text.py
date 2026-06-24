import os
import sys
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core import provider_manager


def fix_text_block(block: str) -> str:
    if not block.strip():
        return block
    messages = [
        {
            "role": "system",
            "content": "Eres un corrector de estilo y ortografía profesional. Tu tarea es recibir un texto en el que los acentos y las 'ñ' se han corrompido transformándose en '' (ej: 'fsico' -> 'físico', 'diseo' -> 'diseño'). También hay algunos errores gramaticales como 'La Tulpas' (debe ser 'Las Tulpas'), 'y incapaz' (debe ser 'e incapaz'), 'un acta' (debe ser 'un acto'). Corrige todos los '' devolviendo la palabra correcta, y corrige los errores gramaticales evidentes. NO CAMBIES LA ESTRUCTURA, NI EL FORMATO MARKDOWN, NI AGREGUES COMENTARIOS. Devuelve SOLO el texto corregido.",
        },
        {"role": "user", "content": block},
    ]
    response = provider_manager.complete(messages)
    cleaned = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()
    return cleaned


def main():
    file_path = os.path.join(
        BASE_DIR, "ensayos_generados", "La_Física_del_Poder", "La_Física_del_Poder.md"
    )

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by double newline to maintain paragraphs/blocks
    blocks = content.split("\n\n")
    fixed_blocks = []

    print(f"Total de bloques a corregir: {len(blocks)}")

    for i, block in enumerate(blocks):
        print(f"Corrigiendo bloque {i+1}/{len(blocks)}...")
        if (
            "" in block
            or "La Tulpas" in block
            or "y incapaz" in block
            or "un acta" in block
        ):
            fixed = fix_text_block(block)
            fixed_blocks.append(fixed)
        else:
            fixed_blocks.append(block)

    final_content = "\n\n".join(fixed_blocks)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(final_content)

    print("Corrección completada. Generando HTML...")

    # Generate HTML again
    try:
        import markdown

        html_content = markdown.markdown(final_content, extensions=["toc"])
        html_file = os.path.join(
            BASE_DIR,
            "ensayos_generados",
            "La_Física_del_Poder",
            "La_Física_del_Poder.html",
        )
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        print("HTML regenerado.")
    except Exception as e:
        print(f"Error HTML: {e}")


if __name__ == "__main__":
    main()
