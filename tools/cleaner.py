import re
import os

book_path = r"f:\Gravity_AI_bridge\libros_generados\La_Voluntad_Soberana\La_Voluntad_Soberana.md"

if os.path.exists(book_path):
    with open(book_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Eliminar bloques <think>...</think>
    cleaned_content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
    # Limpiar espacios o saltos de línea adicionales al inicio de los capítulos
    cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content)

    with open(book_path, "w", encoding="utf-8") as f:
        f.write(cleaned_content.strip())
        
    print("Limpieza completada con éxito. Archivo purificado.")
else:
    print("No se encontró el archivo del libro.")
