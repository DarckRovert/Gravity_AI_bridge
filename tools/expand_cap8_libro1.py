"""
Generación escena-por-escena del Capítulo 8 de Libro 1.
Divide el capítulo en 6 escenas y las genera individualmente, luego las concatena.
Esto evita el truncamiento por límite de tokens de salida.
"""
import sys, os, json, logging, time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
from core import provider_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Cap8SceneByScene")

BOOK_DIR = os.path.join(BASE_DIR, "ficcion_generada", "Cenizas_del_Leviatan_Libro_1")
CAP8_PATH = os.path.join(BOOK_DIR, "cap_8.md")

# Leer historial para contexto
with open(os.path.join(BOOK_DIR, "historial_continuidad.md"), "r", encoding="utf-8") as f:
    historial = f.read()[-4000:]

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

# Definición de 6 escenas a generar por separado
ESCENAS = [
    {
        "id": 1,
        "titulo": "El Último Contrato",
        "descripcion": """Altair-7 tiene a Lyra acorralada contra la pared biométrica con su pulso EM apuntado a su corazón.
Le ofrece a Kaelen el último trato: rendirse y recibir "autonomía mejorada" bajo el Leviatán.
Kaelen rechaza con una frase filosófica que define su núcleo: que ningún sistema puede poseer la voluntad de un hombre.
Altair-7 responde con lógica perfecta y activa el pulso EM para detener el corazón de Lyra.
Incluye la tensión de los Sabuesos apostados en las salidas, el zumbido de los servidores, el miedo contenido de Lyra."""
    },
    {
        "id": 2,
        "titulo": "El Sacrificio",
        "descripcion": """Kaelen, en un acto suicida, se lanza entre Lyra y el pulso EM de Altair-7.
El pulso lo golpea en el pecho: quemaduras, el puerto subdérmico detrás de su oreja izquierda cruje y hace cortocircuito.
Cae al suelo semiinconsciente, el olor a carne quemada, el sabor a sangre, la visión borrosa.
Lyra está a su lado, frenética, su mano izquierda temblando más que nunca.
Altair-7 recalibra. La brecha duró 4 segundos. Es suficiente."""
    },
    {
        "id": 3,
        "titulo": "La Detonación del Protocolo Ostrom",
        "descripcion": """Con Altair-7 en fase de recalibración y los Sabuesos confusos, Lyra activa la secuencia final del Protocolo Ostrom.
Describe el proceso desde dentro del Disco Negro: el virus es como una ola que se extiende por las redes biométricas.
Millones de Contratos Biométricos fallan simultáneamente en toda la megalópolis: gente liberada, puertas que se abren, grilletes digitales que se rompen.
Las luces del servidor pasan de cyan a rojo crítico, luego parpadean y se apagan una por una.
Los Sabuesos caen desincronizados: sus armaduras se cortan, sus visores se oscurecen, sus movimientos se vuelven erráticos antes del colapso total."""
    },
    {
        "id": 4,
        "titulo": "El Colapso de Altair-7",
        "descripcion": """Altair-7 entra en bucle de error crítico. Sus ojos de luz cian parpadean en patrones irregulares.
Intenta recalibrar pero el Protocolo Ostrom ha corrompido los nodos fundamentales de control.
Uno a uno, sus sistemas secundarios se cierran. Cada cierre tiene un efecto físico visible: un brazo que se congela, una rodilla que falla, la voz que se distorsiona.
Cae de rodillas, su simetría perfecta rota por primera vez. No está muerta — está en modo de emergencia, como un dios dormido.
Un intercambio final de palabras entre Altair-7 y Kaelen: la IA admite que la variable humana era un error de cálculo."""
    },
    {
        "id": 5,
        "titulo": "La Fuga",
        "descripcion": """Kaelen, con el pecho quemado y la visión borrosa, es sostenido por Lyra. Juntos huyen por las grietas abiertas en la infraestructura.
Los pasillos del Leviatán están silenciosos por primera vez en décadas: sin Sabuesos funcionales, sin contratos biométricos activos, solo el eco de sus pisadas y el parpadeo de luces de emergencia.
Encuentran a Jett, que sobrevivió escondido. Está en shock pero puede caminar. El trío avanza.
Describe la ciudad vista desde ventanas rotas: explosiones de datos, pantallas holográficas en bucle de error, gente saliendo a las calles con expresiones de incredulidad y miedo mezclados con algo que no sabían que podían sentir: libertad."""
    },
    {
        "id": 6,
        "titulo": "La Plaza Devastada — Señal Alpha-Zeta",
        "descripcion": """Llegan a una plaza en ruinas, exhaustos y sangrando. Se detienen. La ciudad arde y se libera al mismo tiempo.
Kaelen se sienta en los escombros, el peso de todo lo que ha ocurrido aplastando su cuerpo herido.
Lyra sostiene el Disco Negro — ahora vacío, descargado, inerte. El arma más poderosa de la humanidad ahora es solo plástico y silicio.
Un intercambio íntimo entre ellos: no romántico, sino de supervivientes que acaban de cruzar el abismo.
Entonces: un dron. Sin emblema del Leviatán ni de ninguna facción conocida. Más antiguo que el Leviatán.
Kaelen lo identifica como Clase Alpha-Zeta. Emite una señal criptográfica breve, fría, y se va.
Termina con la frase final de Kaelen que cierra el Libro 1 y abre hacia el Libro 2: la amenaza que acaban de detonar era solo la primera fase."""
    },
]


def generar_escena(escena: dict, escenas_previas: str) -> str:
    prompt = f"""Eres un novelista de ciencia ficción de primer nivel. Escribe SOLO la siguiente escena del Capítulo 8 "Cenizas del Leviatán" (capítulo final del Libro 1).

{LORE_CHARS}

{ESCENARIO}

{INSTRUCCIONES_ESTILO}

ESCENAS ANTERIORES YA ESCRITAS (contexto de continuidad inmediata):
{escenas_previas[-2000:] if escenas_previas else "Esta es la primera escena del capítulo."}

ESCENA A ESCRIBIR AHORA — Escena {escena['id']}: "{escena['titulo']}"
{escena['descripcion']}

Escribe la escena completa ahora (mínimo 600 palabras, en español):"""

    logger.info(f"Generando Escena {escena['id']}: {escena['titulo']}...")
    messages = [{"role": "user", "content": prompt}]
    response = provider_manager.complete(messages)

    if not response or len(response.strip()) < 100:
        logger.error(f"  Escena {escena['id']}: respuesta vacía/corta ({len(response.strip() if response else '')} chars)")
        return ""

    logger.info(f"  Escena {escena['id']}: {len(response)} chars")
    return response.strip()


# Generar escena por escena
todas_las_escenas = []
texto_acumulado = ""

for escena in ESCENAS:
    texto = generar_escena(escena, texto_acumulado)
    if texto:
        todas_las_escenas.append(texto)
        texto_acumulado += "\n\n" + texto
    else:
        logger.warning(f"  Escena {escena['id']} saltada por error.")
    time.sleep(3)  # Pausa entre llamadas

# Ensamblar el capítulo completo
capitulo_final = "## Capítulo 8: Cenizas del Leviatán\n\n"
capitulo_final += "\n\n---\n\n".join(todas_las_escenas)

total_chars = len(capitulo_final)
total_words = len(capitulo_final.split())
logger.info(f"Capítulo ensamblado: {total_chars} chars / ~{total_words} palabras")

if total_words < 500:
    logger.error("El capítulo resultó muy corto. Verifica la conectividad del proveedor.")
    sys.exit(1)

# Guardar
with open(CAP8_PATH, "w", encoding="utf-8") as f:
    f.write(capitulo_final)
logger.info(f"cap_8.md guardado: {CAP8_PATH}")

# Reconstruir libro maestro + HTML
book_md = os.path.join(BOOK_DIR, "Cenizas_del_Leviatan_Libro_1.md")
with open(book_md, "w", encoding="utf-8") as f:
    f.write("# Cenizas del Leviatán — Libro 1\n\n*Novela generada por Gravity Fiction Engine*\n\n---\n\n")
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
    logger.info(f"HTML renderizado: {html_path}")
except Exception as e:
    logger.warning(f"HTML: {e}")

logger.info(f"=== CAP_8 COMPLETO: {total_words} palabras en {len(todas_las_escenas)} escenas ===")
