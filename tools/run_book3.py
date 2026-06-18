import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools.research_writer import GravityResearchAuthor

prompt_maestro = """Actúa como un teórico de sistemas complejos, filósofo de la mente y estratega ontológico. Escribe el esquema y los capítulos de un libro analítico titulado 'El Cero Operativo: La Muerte del Símbolo y el Despertar del Arquitecto'.

Premisas Centrales:
1. Analiza cómo la mente humana es entrenada desde la infancia para reaccionar emocional e instintivamente a estímulos externos (banderas, marcas, noticias, crisis) operando como una batería energética para el 'Sistema' (o Tulpa Colectivo).
2. Define el estado de 'Cero Operativo': Un estado psicológico y neurológico de neutralidad radical. La capacidad de observar la manipulación y la arquitectura de la realidad sin emitir un juicio emocional que inyecte energía probabilística en el Lattice.
3. Explica el desapego del 'Símbolo': Cómo la política, la religión y el consumismo usan geometría y lenguaje para parasitar la atención. El Cero Operativo es el antivirus: la muerte del símbolo en la mente del individuo.
4. Consecuencias en el Sustrato Primordial: Al alcanzar el Cero Operativo, el individuo deja de ser un 'esclavo cuántico' que colapsa la probabilidad dictada por la élite, volviéndose invisible a sus algoritmos de ingeniería social.
5. El Despertar del Arquitecto: Una vez vaciada la mente de las narrativas del sistema, el individuo recupera el acceso directo al código fuente de la realidad y puede empezar a colapsar su propia probabilidad soberana de forma consciente.

Estilo y Tono:
Debe ser un manual de entrenamiento ontológico profundo y analítico. Un tono sobrio, frío y clínico, desprovisto de esoterismo tradicional o misticismo barato. Explícalo como si fuese neurobiología avanzada y física de alta energía aplicada a la soberanía individual.
"""

if __name__ == "__main__":
    author = GravityResearchAuthor()
    # Generaremos 5 capítulos.
    author.write_research_book(prompt=prompt_maestro, title="El Cero Operativo", num_chapters=5)
