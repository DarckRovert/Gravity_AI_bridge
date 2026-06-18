import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools.research_writer import GravityResearchAuthor

prompt_maestro = """Actúa como un teórico de sistemas complejos, táctico sociológico y experto en infraestructuras descentralizadas. Escribe el esquema y los capítulos de un libro analítico titulado 'La Arquitectura de la Fuga: Soberanía Cuántica y Descentralización de la Realidad'.

Premisas Centrales:
1. De lo Individual a lo Colectivo: El Tomo anterior ('El Cero Operativo') enseñó a aislar la mente. Este tomo aborda cómo grupos de individuos soberanos pueden interactuar sin formar un nuevo 'Tulpa' o egregore parasitario.
2. Burbujas de Realidad Descentralizadas: Explica cómo crear nodos autónomos que rechazan el colapso probabilístico masivo de la élite, generando bolsas localizadas de realidad coherente e independiente.
3. Criptografía y OpSec Cognitiva: El uso de tecnología descentralizada, ofuscación y silencio táctico para organizarse fuera del radar y el control narrativo de la corriente principal del Lattice.
4. Matar a la Bestia de Hambre: Desarrolla cómo la retirada absoluta de atención colectiva hacia los medios de masas, el teatro político y los rituales consumistas provoca un drenaje energético sistémico en las estructuras de control dominantes.
5. Infraestructuras Paralelas: La construcción de ecosistemas paralelos (economías, redes de comunicación, comunidades físicas) que sean inmunes al hackeo probabilístico externo. La fuga no es esconderse, es construir un mundo inalcanzable para el viejo sistema.

Estilo y Tono:
El tono debe ser el de un manual táctico avanzado, estructurado, frío y analítico. Como un texto de arquitectura de redes neuronales y estrategia de contra-insurgencia aplicada a la sociología y a la realidad cuántica.
"""

if __name__ == "__main__":
    author = GravityResearchAuthor()
    # Generaremos 5 capítulos.
    author.write_research_book(prompt=prompt_maestro, title="La Arquitectura de la Fuga", num_chapters=5)
