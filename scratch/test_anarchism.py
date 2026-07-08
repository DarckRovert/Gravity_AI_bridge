import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools.research_writer import GravityResearchAuthor

author = GravityResearchAuthor()

prompt = """
Escribe un ensayo académico-filosófico estructurado en 3 capítulos sobre 'El Anarquismo como Madurez Colectiva'.
Perspectiva a mantener:
El anarquismo no debe ser presentado como caos o rebelión adolescente, sino como un 'oficio de la libertad', una praxis de responsabilidad extrema sin coerción. 
Utiliza la metáfora de la 'Zona Ágora' donde la libertad radical exige una ética superior de organización descentralizada. 
Toma como referencias a Proudhon (reciprocidad y justicia económica en intercambios), Bakunin (fuerza pasional pero con la advertencia de que la destrucción no crea, se necesita disciplina práctica), Elinor Ostrom (gobernar sin gobierno, gestión de bienes comunes bajo reglas de sostenibilidad local) y Kropotkin (apoyo mutuo como factor de evolución).
Tono: Clínico, analítico, deductivo y sobrio.
"""

author.write_research_book(
    prompt=prompt,
    title="La Madurez de la Libertad",
    num_chapters=3,
    review_outline=False
)
