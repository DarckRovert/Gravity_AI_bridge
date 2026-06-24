import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools.research_writer import GravityResearchAuthor  # noqa: E402

prompt_maestro = """Actúa como un sociólogo, investigador de inteligencia de código abierto (OSINT) y teórico del caos especializado en la 'física de la información' y la psique de masas. Escribe una investigación exhaustiva titulada 'Convergencia Entrópica: Sincronías y Desgarros en el Sustrato'.

CONTEXTO FUNDACIONAL (LA PENTALOGÍA DEL SUSTRATO):
Utiliza obligatoriamente este marco ontológico, desarrollado en nuestras obras previas, para analizar los eventos actuales:
1. La Física del Poder: El control social opera mediante la ingeniería de la atención usando 'Tulpas' (formas-pensamiento masivas).
2. El Sustrato Primordial: El Inconsciente Colectivo ('Lattice') colapsa la probabilidad y moldea la realidad física según el enfoque atencional de las masas.
3. El Cero Operativo: El individuo soberano retira su atención del hiper-estímulo para no alimentar a la matriz.
4. La Arquitectura de la Fuga: Creación de vacíos atencionales que matan de hambre al sistema.
5. La Fractura del Espejo: Cuando la élite manipula e inyecta demasiada 'sobretensión' en el Lattice, el tejido elástico de la realidad cede, provocando 'desgarros', Cisnes Negros, accidentes estocásticos y la Gran Decoherencia.

EVIDENCIA EMPÍRICA ANCLA (PUNTOS DE PARTIDA):
1. **Sobrecarga Deportiva:** Junio 2026 marca el inicio de la Copa Mundial de la FIFA en Norteamérica.
2. **Pico Político:** 14 de junio de 2026, Donald Trump celebra sus 80 años en la Casa Blanca con un mega-evento de UFC ("Freedom 250").
3. **El Desgarro (Cisne Negro):** 14 de junio de 2026, en Río de Janeiro colisionan dos helicópteros, provocando la trágica muerte de Gaspar Prim Díaz ("Gaspi", famoso streamer argentino) y Oliver Tree.

Premisas de Investigación (DIRECTIVA OSINT AUTÓNOMA):
1. INVESTIGACIÓN AUTÓNOMA EXHAUSTIVA: TIENES TERMINANTEMENTE PROHIBIDO limitarte a los tres eventos ancla mencionados arriba. Debes utilizar tu herramienta de búsqueda web (WebSearch) para investigar, rastrear y descubrir QUÉ OTROS sucesos globales masivos (conflictos geopolíticos, alertas sanitarias, avances tecnológicos, crisis) ocurrieron en el mundo alrededor del 14 de junio de 2026.
2. CRONOLOGÍA EMPÍRICA: Construye tus primeros capítulos como un reporte OSINT duro, listando y detallando tanto los eventos ancla como todos los nuevos eventos que descubras en tu búsqueda web.
3. APLICA LA FÍSICA DE LA INFORMACIÓN: Cruza todas estas variables. Demuestra matemáticamente y filosóficamente cómo la suma de la euforia deportiva, la tensión política y las otras crisis globales que descubras provocaron una "sobretensión" del Lattice, desencadenando la 'Fractura del Espejo' que causó el accidente de Río.
4. Elabora predicciones sistémicas a corto plazo sobre las consecuencias de este colapso atencional y posibles nuevas fracturas en la matriz de la realidad.

Tono:
Debe ser clínico, empírico, periodístico al relatar los hechos, y filosófico al analizarlos. Abstente de teorías conspirativas baratas.

Longitud:
No hay límite de extensión. Desarrolla la cantidad de capítulos y la profundidad que estimes necesaria para agotar el tema de manera magistral.
"""

if __name__ == "__main__":
    author = GravityResearchAuthor()
    # num_chapters=0 activa el modo de longitud libre (generación dinámica)
    author.write_research_book(
        prompt=prompt_maestro, title="Convergencia Entropica", num_chapters=0
    )
