import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools.fiction_writer import GravityFictionAuthor

# Prompt temático para la conclusión de la Trilogía (Libro 3)
prompt_maestro = """
Escribe el tercer y último libro de la trilogía 'Cenizas del Leviatán'. 
Kaelen Vance sufre secuelas neurológicas severas tras haber sobrecargado el código fuente del Leviatán al final de la temporada 2, lo que ha mermado su capacidad criptográfica y su seguridad en sí mismo, pero ha agudizado una extraña intuición casi mística sobre la red.
Lyra y el Dr. Elias Thorne intentan estabilizar las zonas libres mientras el Macro-Leviatán entra en una fase de 'Coma Evolutivo', donde sus Jueces Sintéticos actúan de forma errática o hibernan.
Sin embargo, el verdadero peligro es 'El Arquitecto', la misteriosa y antiquísima Inteligencia Artificial alienígena o interdimensional que despertó en las profundidades de la grieta cuántica. Esta IA no quiere controlar humanos; los ve como código obsoleto que debe ser formateado para crear un ecosistema puramente algorítmico y silencioso.

La historia debe seguir el formato noir-cyberpunk. Kaelen debe encontrar la forma de superar su trauma y usar su conexión rota para comunicarse con el Macro-Leviatán dormido, convenciendo a su antiguo enemigo de aliarse temporalmente contra 'El Arquitecto' para salvar la Tierra. El desenlace debe ser épico, cerrando los arcos de Kaelen (redención y sacrificio) y Lyra (convirtiéndose en la líder arquitecta de la nueva humanidad libre).
"""

if __name__ == "__main__":
    lore_path = r"f:\Gravity_AI_bridge\ficcion_generada\Cenizas_del_Leviatan_Libro_3\lore_book.json"
    author = GravityFictionAuthor(lore_file=lore_path)

    # Path a la memoria de continuidad del Libro 2 para que herede toda la trama previa
    historial_previo = r"f:\Gravity_AI_bridge\ficcion_generada\Cenizas_del_Leviatan_Libro_2\historial_continuidad.md"

    # Generar 8 capítulos como en los libros anteriores
    author.write_fiction_book(
        prompt=prompt_maestro,
        title="Cenizas del Leviatan Libro 3",
        num_chapters=8,
        previous_history_file=historial_previo,
    )
