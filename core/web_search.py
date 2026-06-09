"""
Gravity AI — Web Search Module V15.2 PRO
Realiza búsquedas autónomas en DuckDuckGo y scrapea contenido para inyectar conocimiento enriquecido.
Garantiza tolerancia a fallos, reintentos de red y total seguridad multihilo.
"""

import urllib.request
import urllib.parse
import re
import html
import socket
from typing import List, Tuple, Dict, Any

from core.logger import log
from core.firecrawl_scraper import scrape_url, _request_with_retry


def search_and_scrape(query: str, max_results: int = 2) -> str:
    """
    Busca en DuckDuckGo de forma thread-safe y hace scraping de los resultados principales.
    
    Aplica exclusión de fallos de red esporádicos mediante reintentos con retroceso exponencial.
    Sanitiza de forma robusta los snippets y páginas descargadas para inyección limpia en el LLM.
    
    Args:
        query: Término o pregunta a buscar.
        max_results: Cantidad máxima de fuentes web a consultar.
        
    Returns:
        Cadena de texto estructurada con la información extraída de las fuentes web principales.
    """
    if not query or not query.strip():
        return ""

    url: str = "https://html.duckduckgo.com/html/"
    payload: bytes = urllib.parse.urlencode({"q": query, "kl": "es-es"}).encode("utf-8")
    
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GravityAI/15.1 (KHTML, like Gecko)",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )
    
    try:
        # Reutilizar el sistema de reintentos robusto del scraper
        with _request_with_retry(req, timeout=15, max_retries=3) as resp:
            content = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        log.warning(f"[WebSearch] Error fetching search results for query '{query}': {e}")
        # Silenciar y retornar vacío defensivamente para no romper la tubería del agente
        return ""
        
    results: List[Tuple[str, str]] = []
    # Match snippets de DuckDuckGo de forma estructurada
    pattern = re.compile(r'<a class="result__snippet[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
    
    for match in pattern.finditer(content):
        url_match = match.group(1).strip()
        # Resolver redirección interna de DuckDuckGo uddg
        if url_match.startswith("//duckduckgo.com/l/?uddg="):
            try:
                url_match = urllib.parse.unquote(url_match.split("uddg=")[1].split("&")[0])
            except Exception:
                continue
                
        snippet_text = html.unescape(re.sub(r'<[^>]+>', '', match.group(2).strip()))
        results.append((url_match, snippet_text))
        if len(results) >= max_results:
            break
            
    if not results:
        log.info(f"[WebSearch] No results found on DuckDuckGo for query: '{query}'")
        return ""
        
    knowledge: List[str] = []
    for link, snippet in results:
        # Excluir procesamiento de videos directos en scraping de texto
        if "youtube.com" in link or "youtu.be" in link:
            knowledge.append(f"--- FUENTE: {link} ---\n{snippet}\n")
            continue
            
        try:
            scrape_res = scrape_url(link)
            if scrape_res.get("ok") and len(scrape_res.get("content", "")) > 50:
                text = scrape_res.get("content", "")[:3000]
                knowledge.append(f"--- FUENTE: {link} ---\n{text}\n")
            else:
                knowledge.append(f"--- FUENTE: {link} ---\n{snippet}\n")
        except Exception as e:
            log.debug(f"[WebSearch] Failed to scrape {link}: {e}. Falling back to snippet.")
            knowledge.append(f"--- FUENTE: {link} ---\n{snippet}\n")
            
    return "\n".join(knowledge)

