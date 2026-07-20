"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — MARKET RESEARCHER V16.0 PRO [Diamond-Tier Edition]             ║
║  Agente de Investigación de Mercado (Competitor Analysis)                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

Evolución de Gravity basada en el Hack 4 (Market Research con Múltiples Agentes).
Busca y analiza la competencia en la web de forma automática, estructurando
briefings competitivos mediante los mejores LLMs locales disponibles.
"""

from typing import Dict, List
from core.logger import log
from core.web_search import search_and_scrape
from core.provider_manager import get_best, complete


def analyze_competitors(topic: str) -> str:
    """
    Busca los videos más populares sobre el tema y le pide al LLM que analice
    qué es lo que está funcionando (ángulos, hooks) para dárselo al guionista.

    Args:
        topic: El tema o nicho a investigar.

    Returns:
        Un briefing competitivo estructurado en formato Markdown, o una cadena vacía en caso de error.
    """
    if not topic or not topic.strip():
        log.warning("[MarketResearch] Tema vacío o inválido proporcionado.")
        return ""

    log.info(f"[MarketResearch] Analizando a la competencia para: '{topic}'")

    # 1. Buscar en DuckDuckGo resultados de YouTube y artículos top
    # Sanitizamos el topic para no exceder los límites de DuckDuckGo / SearXNG
    safe_topic = topic.split('.')[0][:80].strip() if topic else ""
    query: str = f"{safe_topic} youtube video"
    try:
        raw_data: str = search_and_scrape(query, max_results=3)
    except Exception as search_err:
        log.error(
            f"[MarketResearch] Error al realizar búsqueda y raspado: {search_err}"
        )
        return ""

    if not raw_data or not raw_data.strip():
        log.warning(
            "[MarketResearch] No se encontró información de la competencia en la web."
        )
        return ""

    # 2. Analizar la data con LLM
    prompt: str = (
        f"Eres un Analista de Mercado y Estratega de YouTube.\n"
        f"Tu cliente quiere hacer un video sobre: '{topic}'.\n"
        "Aquí están los datos que hemos recopilado sobre lo que ya existe y es popular (Competencia):\n"
        f"{raw_data}\n\n"
        "Por favor, redacta un 'Briefing Competitivo' (máximo 150 palabras) indicando:\n"
        "1. Qué ángulos funcionan mejor.\n"
        "2. Qué errores evitar o qué información falta en esos videos.\n"
        "3. Una recomendación directa para que el guionista de este nuevo video los supere en retención."
    )

    best_prov, best_model = get_best()
    if not best_prov or not best_model:
        log.error(
            "[MarketResearch] No hay proveedores activos o configurados para el análisis."
        )
        return ""

    messages: List[Dict[str, str]] = [{"role": "user", "content": prompt}]

    try:
        result: str = complete(
            messages=messages,
            model=best_model,
            provider=best_prov.name,
            options={"temperature": 0.5, "max_tokens": 400},
        )
        if not result or not result.strip():
            log.warning("[MarketResearch] Respuesta vacía del LLM.")
            return ""

        log.info("[MarketResearch] Briefing competitivo generado exitosamente.")
        return f"\n\n[BRIEFING COMPETITIVO (MARKET RESEARCH)]:\n{result}\n"
    except Exception as e:
        log.error(f"[MarketResearch] Error analizando competidores vía LLM: {e}")
        return ""
