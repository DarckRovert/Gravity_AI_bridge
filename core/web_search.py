"""
Gravity AI — Web Search Module
Realiza búsquedas autónomas en internet para recopilar conocimiento antes de generar contenido.
"""
import urllib.request
import urllib.parse
import re
import html
from core.firecrawl_scraper import scrape_url

def search_and_scrape(query: str, max_results: int = 2) -> str:
    """Busca en DuckDuckGo y hace scraping de los resultados principales para extraer conocimiento."""
    url = "https://html.duckduckgo.com/html/"
    data = urllib.parse.urlencode({"q": query, "kl": "es-es"}).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GravityAI/10.3",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        # Silenciar el error y retornar vacío para no inyectar basura en el prompt del LLM
        return ""
        
    results = []
    for match in re.finditer(r'<a class="result__snippet[^>]*href="([^"]+)"[^>]*>(.*?)</a>', content, re.IGNORECASE | re.DOTALL):
        url_match = match.group(1).strip()
        if url_match.startswith("//duckduckgo.com/l/?uddg="):
            url_match = urllib.parse.unquote(url_match.split("uddg=")[1].split("&")[0])
            
        results.append(url_match)
        if len(results) >= max_results:
            break
            
    if not results:
        return ""
        
    knowledge = []
    for link in results:
        scrape_res = scrape_url(link)
        if scrape_res.get("ok"):
            text = scrape_res.get("content", "")[:3000]
            knowledge.append(f"--- FUENTE: {link} ---\n{text}\n")
            
    return "\n".join(knowledge)
