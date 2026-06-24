import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools.research_writer import GravityResearchAuthor  # noqa: E402

prompt_maestro = """Actúa como un teórico de sistemas complejos, historiador analítico y arquitecto estructural. Escribe el esquema y los capítulos de un libro analítico titulado 'El Sustrato Primordial: La Matriz de Posibilidad Infinita'.

Premisas Centrales:
1. Unifica todos los nombres históricos (El Lattice de Grinberg, el Akasha, el Tao, el Cero Absoluto, Dios) no como conceptos místicos, sino como una 'Matriz Funcional' o 'Sustrato Primordial': el hardware cuántico del universo. Religiones y físicos describen lo mismo usando distinto software.
2. Analiza la 'Magia' como una Ingeniería de Sincronicidades. Explica cómo la consciencia humana colapsa probabilidades. 
CRÍTICO: Esto ya no será una explicación de los fenómenos internos de la mente afectada por la realidad, sino AL REVÉS: cómo la mente colectiva podría estar afectando o moldeando la realidad material objetiva de manera inconsciente, y cómo las élites abusan de este fenómeno.
3. FUNDAMENTAL: Documenta con eventos reales. Exige la búsqueda de correlaciones entre fechas críticas, ciclos astronómicos, numerología y lugares con carga simbólica (geografía sagrada) usados en eventos de alto impacto geopolítico (ejemplos históricos reales comprobables, como asesinatos estratégicos, atentados o tratados).
4. Explica la 'Invisibilidad del Método': cómo la élite usa el sesgo materialista de la academia como camuflaje para operar esta ciencia oculta, que es en realidad un dominio sobre la atención y la probabilidad.
5. Mantén un tono de 'Arquitecto' frío e impecable. Despoja al Lattice de jerga exclusivamente científica para hacerlo universal, y evita el misticismo religioso. Habla del código fuente de la realidad.

La estructura obligatoria es:
Capítulo 1: El Problema de la Nomenclatura y la Unificación del Concepto. (El hardware del universo vs el software de la cultura).
Capítulo 2: La Geometría de los Eventos. Analiza patrones históricos reales, fechas de atentados o incidentes estratégicos (usa resultados web reales para fechas y localizaciones).
Capítulo 3: La Tecnología del Ritual. Cómo la repetición y el simbolismo masivo inyectan señales en el Lattice.
Capítulo 4: La Anomalía del Poder y el Sesgo Materialista (El velo de invisibilidad científica).
Capítulo 5: La Potencialidad Infinita (Conclusión analítica sobre cómo los individuos pueden recuperar el código fuente de la probabilidad).
"""

if __name__ == "__main__":
    author = GravityResearchAuthor()
    # Generaremos 5 capítulos.
    author.write_research_book(
        prompt=prompt_maestro, title="El Sustrato Primordial", num_chapters=5
    )
