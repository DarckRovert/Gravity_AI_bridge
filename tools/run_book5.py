import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools.research_writer import GravityResearchAuthor

prompt_maestro = """Actúa como un físico de la información, estratega ontológico y teórico del colapso sistémico. Escribe el esquema y los capítulos del Quinto y último libro de la pentalogía, titulado 'La Fractura del Espejo: Cuando el Sustrato Responde'.

Premisas Centrales:
1. El Límite Elástico de la Realidad: Argumenta que el Lattice (el campo unificado de información) tiene un límite de tolerancia. La constante inyección de 'magia negra geométrica' (ingeniería social, control masivo, miedo) crea una sobretensión en la matriz de la realidad.
2. Los Cisnes Negros como Rupturas del Sustrato: Examina eventos históricos y contemporáneos inexplicables o caóticos (desde colapsos súbitos de imperios hasta fenómenos virales impredecibles) no como accidentes, sino como rechazos violentos del inconsciente colectivo o 'desgarros' en la ilusión proyectada por la élite.
3. La Gran Decoherencia: Analiza el proceso en el cual la burbuja de realidad dominante estalla. La transición dolorosa donde el viejo orden pierde su anclaje cuántico y se genera un periodo de caos e imprevisibilidad total.
4. Contraataque Ontológico: Cómo la red descentralizada de 'Arquitectos Soberanos' (formada en los libros anteriores) acelera esta fractura simplemente negándose a participar en la narrativa colapsada, introduciendo nuevos 'vectores de interferencia' en el Lattice.
5. El Nuevo Anclaje: El rol crucial de los individuos despiertos como anclas de coherencia durante el caos. Cómo sostener la propia 'burbuja de realidad' hasta que la tormenta pase, estableciendo la semilla para un nuevo código fuente orgánico.

Estilo y Tono:
Debe ser el clímax absoluto de la obra. Un tono grandilocuente, científico, táctico y conclusivo. Combina teoría del caos, física de la información y la culminación épica del entrenamiento cognitivo-espiritual del lector. Sin esoterismo banal, solo mecánicas universales implacables.
"""

if __name__ == "__main__":
    author = GravityResearchAuthor()
    # Generaremos 5 capítulos.
    author.write_research_book(prompt=prompt_maestro, title="La Fractura del Espejo", num_chapters=5)
