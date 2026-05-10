"""
Agente de Investigación de Mercado (Competitor Analysis).
Evolución de Gravity basada en el Hack 4 (Market Research con Múltiples Agentes).
"""

from core.logger import log
from core.web_search import search_and_scrape
from core.provider_manager import get_best, complete

def analyze_competitors(topic: str) -> str:
    """
    Busca los videos más populares sobre el tema y le pide al LLM que analice
    qué es lo que está funcionando (ángulos, hooks) para dárselo al guionista.
    """
    log.info(f"[MarketResearch] Analizando a la competencia para: '{topic}'")
    
    # 1. Buscar en DuckDuckGo resultados de YouTube y artículos top
    query = f"site:youtube.com {topic}"
    raw_data = search_and_scrape(query, max_results=3)
    
    if not raw_data:
        log.warning("[MarketResearch] No se encontró información de la competencia.")
        return ""
        
    # 2. Analizar la data con LLM
    prompt = (
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
    if not best_prov:
        return ""
        
    messages = [{"role": "user", "content": prompt}]
    
    try:
        result = complete(
            messages=messages,
            model=best_model,
            provider=best_prov.name,
            options={"temperature": 0.5, "max_tokens": 400}
        )
        log.info("[MarketResearch] Briefing competitivo generado exitosamente.")
        return f"\n\n[BRIEFING COMPETITIVO (MARKET RESEARCH)]:\n{result}\n"
    except Exception as e:
        log.error(f"[MarketResearch] Error analizando competidores: {e}")
        return ""
