"""
Gravity AI — Web Search Module V16.0 PRO
Realiza búsquedas autónomas en DuckDuckGo y scrapea contenido para inyectar conocimiento enriquecido.
Garantiza tolerancia a fallos, reintentos de red y total seguridad multihilo.
"""

import urllib.request
import urllib.parse
import re
import html
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.logger import log
from core.firecrawl_scraper import scrape_url, _request_with_retry



# Instancias públicas de SearXNG con JSON habilitado
# Se rotan aleatoriamente para distribuir carga y evitar bloqueos por IP
_SEARXNG_INSTANCES = [
    "https://searx.be",
    "https://search.sapti.me",
    "https://searx.tiekoetter.com",
    "https://searxng.site",
    "https://search.privacyguides.net",
    "https://searx.work",
    "https://priv.au",
]

def _searxng_fallback(query: str, max_results: int = 2) -> List[Tuple[str, str]]:
    """
    Fallback a instancias públicas de SearXNG cuando DuckDuckGo falla.
    Retorna lista de (url, snippet) igual que el parser de DDG.
    Prueba instancias en orden aleatorio para distribuir la carga.
    """
    import json as _json
    import random
    encoded_q = urllib.parse.quote(query)
    results: List[Tuple[str, str]] = []
    
    # Rotar instancias aleatoriamente para evitar rate limiting en una sola
    instances = list(_SEARXNG_INSTANCES)
    random.shuffle(instances)

    for instance in instances:
        try:
            url = f"{instance}/search?q={encoded_q}&format=json&language=es-ES&categories=general"
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
                }
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                data = _json.loads(raw)
            
            for r in data.get("results", [])[:max_results]:
                link = r.get("url", "")
                snippet = r.get("content", r.get("title", ""))
                if link and snippet and len(snippet) > 20:
                    results.append((link, snippet))
            
            if results:
                log.info(f"[WebSearch] SearXNG ({instance}) OK: {len(results)} resultados.")
                return results

        except Exception as e:
            log.debug(f"[WebSearch] SearXNG {instance} falló: {e}")
            continue

    return results


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

    url: str = "https://lite.duckduckgo.com/lite/"
    payload: bytes = urllib.parse.urlencode({"q": query, "kl": "es-es"}).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    try:
        # Reutilizar el sistema de reintentos robusto del scraper
        with _request_with_retry(req, timeout=15, max_retries=3) as resp:
            content = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        log.warning(
            f"[WebSearch] Error fetching search results for query '{query}': {e}"
        )
        # Silenciar y retornar vacío defensivamente para no romper la tubería del agente
        return ""

    results: List[Tuple[str, str]] = []
    # Match snippets de DuckDuckGo de forma estructurada
    pattern = re.compile(
        r'<a class="result__snippet[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )

    for match in pattern.finditer(content):
        url_match = match.group(1).strip()
        # Resolver redirección interna de DuckDuckGo uddg
        if url_match.startswith("//duckduckgo.com/l/?uddg="):
            try:
                url_match = urllib.parse.unquote(
                    url_match.split("uddg=")[1].split("&")[0]
                )
            except Exception:
                continue

        snippet_text = html.unescape(re.sub(r"<[^>]+>", "", match.group(2).strip()))
        results.append((url_match, snippet_text))
        if len(results) >= max_results:
            break

    if not results:
        log.info(f"[WebSearch] No results found on DuckDuckGo for query: '{query}'. Intentando SearXNG...")
        results = _searxng_fallback(query, max_results)
        if not results:
            log.warning(f"[WebSearch] SearXNG también falló para: '{query}'")
            return ""

    knowledge: List[str] = []
    
    def process_result(idx: int, link: str, snippet: str) -> str:
        # Excluir procesamiento de videos directos en scraping de texto
        if "youtube.com" in link or "youtu.be" in link:
            return f"[{idx}] FUENTE: {link}\nRESUMEN: {snippet}\n"

        try:
            scrape_res = scrape_url(link)
            if scrape_res.get("ok") and len(scrape_res.get("content", "")) > 50:
                text = scrape_res.get("content", "")[:3000]
                return f"[{idx}] FUENTE: {link}\nTEXTO: {text}\n"
            else:
                return f"[{idx}] FUENTE: {link}\nRESUMEN: {snippet}\n"
        except Exception as e:
            log.debug(f"[WebSearch] Failed to scrape {link}: {e}. Falling back to snippet.")
            return f"[{idx}] FUENTE: {link}\nRESUMEN: {snippet}\n"

    with ThreadPoolExecutor(max_workers=max_results) as executor:
        futures = {
            executor.submit(process_result, idx + 1, link, snippet): (idx + 1)
            for idx, (link, snippet) in enumerate(results)
        }
        # Asegurar orden numérico
        sorted_results = []
        for future in as_completed(futures):
            sorted_results.append((futures[future], future.result()))
        
        sorted_results.sort(key=lambda x: x[0])
        knowledge = [res[1] for res in sorted_results]

    return "\n".join(knowledge)

