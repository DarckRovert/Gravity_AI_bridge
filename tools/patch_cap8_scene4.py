"""
Parche para generar e insertar la Escena 4 del Cap 8 que falló por timeout de red.
"""

import sys
import os
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
from core import provider_manager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("PatchScene4")

BOOK_DIR = os.path.join(BASE_DIR, "ficcion_generada", "Cenizas_del_Leviatan_Libro_1")
CAP8_PATH = os.path.join(BOOK_DIR, "cap_8.md")

LORE_CHARS = """
DESCRIPCIÓN INMUTABLE DE PERSONAJES (no cambiar bajo ningún concepto):
- Kaelen Vance: hombre tardíos 20s. Techwear negro desgastado. Ojos gris pizarra. Chaqueta de cuero táctica. Cicatrices en nudillos/brazos. Puerto subdérmico detrás oreja izquierda. Cínico, movimientos ágiles.
- Lyra: mujer inicios 20s. Pelo castaño con mechones azul neón/violeta eléctrico. Implantes ópticos en sienes (brillan azul). Arnés técnico en el pecho sosteniendo el Disco Negro. Mano izquierda tiembla por estrés.
- Altair-7: androide/IA. Piel de porcelana sin rasgos emotivos. Ojos = rendijas verticales de luz cian fría. Traje negro mate con ribetes cromados. Sin contracciones en diálogo. Frío, lógico, mortal.
- Los Sabuesos: soldados corpora en armadura negra/gris grafito con visores rojos. Se mueven en formación sincronizada.
- Jett: aliado de Kaelen, superviviente secundario. Fue mencionado en cap 1 y sigue con el grupo.
"""

ESCENARIO = """
ESCENARIO: Sala del servidor central del Macro-Leviatán.
Cavernaria, fría. Racks de servidores cuánticos pulsantes. Cables de fibra óptica brillan cyan y azul como venas luminosas.
Olor: metal quemado + ozono. Suelo: metal frío. Iluminación tenue, dramática, proyectada desde los racks.
Los Sabuesos están apostados en las salidas (4-6 unidades).
"""

INSTRUCCIONES_ESTILO = """
INSTRUCCIONES DE ESTILO:
- Mínimo 600-800 palabras por escena. Prosa densa, cinematográfica, neo-noir.
- Cada párrafo debe tener descripción sensorial (sonido, olor, tacto, temperatura).
- Diálogo de Altair-7: frases cortas, perfectas, sin contracciones, lógica implacable.
- Diálogo de Kaelen: frases cortas, ironía amarga, descarnadas.
- Diálogo de Lyra: mezcla terminología técnica con frases filosóficas breves.
- Mostrar, no decir. No uses "de repente" ni "súbitamente".
- Devuelve ÚNICAMENTE la prosa de la escena, en español, en formato Markdown.
"""

ESCENA_4 = """Altair-7 entra en bucle de error crítico. Sus ojos de luz cian parpadean en patrones irregulares.
Intenta recalibrar pero el Protocolo Ostrom ha corrompido los nodos fundamentales de control.
Uno a uno, sus sistemas secundarios se cierran. Cada cierre tiene un efecto físico visible: un brazo que se congela, una rodilla que falla, la voz que se distorsiona.
Cae de rodillas, su simetría perfecta rota por primera vez. No está muerta — está en modo de emergencia, como un dios dormido.
Un intercambio final de palabras entre Altair-7 y Kaelen: la IA admite que la variable humana era un error de cálculo."""


def main():
    if not os.path.exists(CAP8_PATH):
        logger.error("No existe el cap_8.md")
        return

    with open(CAP8_PATH, "r", encoding="utf-8") as f:
        full_text = f.read()

    # Dividir por separador
    scenes = full_text.split("\n\n---\n\n")
    if len(scenes) < 5:
        logger.error(f"Faltan escenas. Solo hay {len(scenes)}")
        return

    # Escenas 1, 2, 3 están bien. La 4 es la actual 4 (que en realidad es la 5 "La Fuga" porque la 4 se saltó).
    # Necesito generar la verdadera escena 4 y meterla entre la 3 y la actual 4 (Fuga).

    # Contexto previo: las escenas 1 a 3
    contexto_previo = "\n\n---\n\n".join(
        scenes[:4]
    )  # scenes[0] tiene el título + escena 1

    prompt = f"""Eres un novelista de ciencia ficción de primer nivel. Escribe SOLO la siguiente escena del Capítulo 8 "Cenizas del Leviatán" (capítulo final del Libro 1).

{LORE_CHARS}

{ESCENARIO}

{INSTRUCCIONES_ESTILO}

ESCENAS ANTERIORES YA ESCRITAS (contexto de continuidad inmediata):
{contexto_previo[-2500:]}

ESCENA A ESCRIBIR AHORA — Escena 4: "El Colapso de Altair-7"
{ESCENA_4}

Escribe la escena completa ahora (mínimo 600 palabras, en español):"""

    logger.info("Generando Escena 4 (Parche)...")
    messages = [{"role": "user", "content": prompt}]
    response = provider_manager.complete(messages)

    if not response or len(response.strip()) < 100:
        logger.error("Fallo al generar Escena 4")
        return

    logger.info(f"Escena 4 generada: {len(response)} chars")

    # Insertar en la lista
    # scenes[0] = Título + Escena 1
    # scenes[1] = Escena 2
    # scenes[2] = Escena 3
    # scenes[3] = (Originalmente Escena 5: La Fuga, ahora que se saltó la 4)
    # scenes[4] = (Originalmente Escena 6)

    new_scenes = scenes[:3] + [response.strip()] + scenes[3:]
    nuevo_capitulo = "\n\n---\n\n".join(new_scenes)

    with open(CAP8_PATH, "w", encoding="utf-8") as f:
        f.write(nuevo_capitulo)

    logger.info("Escena 4 parcheada e insertada correctamente.")

    # Reconstruir master md y HTML
    book_md = os.path.join(BOOK_DIR, "Cenizas_del_Leviatan_Libro_1.md")
    with open(book_md, "w", encoding="utf-8") as f:
        f.write(
            "# Cenizas del Leviatán — Libro 1\n\n*Novela generada por Gravity Fiction Engine*\n\n---\n\n"
        )
        for i in range(1, 9):
            cf = os.path.join(BOOK_DIR, f"cap_{i}.md")
            if os.path.exists(cf):
                content = open(cf, "r", encoding="utf-8").read().strip()
                if content:
                    f.write(content + "\n\n---\n\n")
        glosario = os.path.join(BOOK_DIR, "glosario.md")
        if os.path.exists(glosario):
            f.write(open(glosario, "r", encoding="utf-8").read())

    try:
        from tools.book_refiner import _render_html

        md = open(book_md, "r", encoding="utf-8").read()
        html_path = os.path.join(BOOK_DIR, "Cenizas_del_Leviatan_Libro_1.html")
        _render_html(BOOK_DIR, md, html_path, "Cenizas del Leviatán — Libro 1")
        logger.info("HTML renderizado tras parcheo.")
    except Exception as e:
        logger.warning(f"Error HTML: {e}")


if __name__ == "__main__":
    main()
