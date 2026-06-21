"""
Gravity AI — Capa de Herramientas: Buscador Web de Resiliencia Extrema (WebSearch)
Estándar: Diamond-Tier (Tipado estricto, sin API-key obligatoria y tolerancia total a fallos de red).
"""
import re
import urllib.request
import urllib.parse
import json
from typing import List, Dict, Any, Optional
from tools.base_tool import Tool, ToolResult

DDG_URL: str = "https://html.duckduckgo.com/html/"
BRAVE_URL: str = "https://api.search.brave.com/res/v1/web/search"
MAX_RES: int = 10


def fetch_page_text(url: str, max_chars: int = 3000) -> str:
    """
    Descarga y limpia el HTML de una URL, retornando texto plano.
    Usado para recuperación profunda de contenido más allá del snippet.
    """
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GravityAI/10.3"}
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = r.read(max_chars * 6).decode("utf-8", errors="ignore")
        # Eliminar scripts, styles, tags HTML (permitiendo que terminen abruptamente si el buffer se cortó)
        raw = re.sub(r'<script[^>]*>.*?(?:</script>|$)', '', raw, flags=re.DOTALL | re.IGNORECASE)
        raw = re.sub(r'<style[^>]*>.*?(?:</style>|$)', '', raw, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', raw)
        text = re.sub(r'\s{2,}', ' ', text).strip()
        return text[:max_chars]
    except Exception as e:
        return f"[fetch_page_text error: {e}]"


def _ddg_search(query: str) -> List[Dict[str, str]]:
    """
    Realiza una búsqueda web a través de la interfaz HTML de DuckDuckGo sin requerir clave de API.
    Utiliza expresiones regulares estructuradas para extraer títulos, URLs y resúmenes.

    Parámetros:
        query (str): Término o frase de búsqueda en la web.

    Retorna:
        List[Dict[str, str]]: Lista de diccionarios que contienen 'title', 'url' y 'snippet'.
    """
    data: bytes = urllib.parse.urlencode({"q": query, "kl": "es-es"}).encode()
    req = urllib.request.Request(DDG_URL, data=data, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GravityAI/10.3",
        "Content-Type": "application/x-www-form-urlencoded",
    })
    try:
        # Timeout aumentado a 10 segundos para máxima resiliencia en conexiones inestables
        with urllib.request.urlopen(req, timeout=10) as r:
            html: str = r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return [{"title": "Error de Red", "url": "", "snippet": f"No se pudo consultar DuckDuckGo: {str(e)}"}]

    results: List[Dict[str, str]] = []
    
    # Análisis robusto mediante expresiones regulares eficientes
    titles: List[str] = re.findall(r'class="result__title"[^>]*>.*?<a[^>]*>(.*?)</a>', html, re.DOTALL)
    urls: List[str] = re.findall(r'class="result__url"[^>]*>\s*(.*?)\s*</a>', html, re.DOTALL)
    snippets: List[str] = re.findall(r'class="result__snippet"[^>]*>(.*?)</(?:a|span|div)>', html, re.DOTALL)

    for i in range(min(MAX_RES, len(titles))):
        title_raw: str = re.sub(r"<[^>]+>", "", titles[i]).strip()
        title: str = re.sub(r"\s+", " ", title_raw)
        
        url: str = urls[i].strip() if i < len(urls) else ""
        
        snippet_raw: str = snippets[i].strip() if i < len(snippets) else ""
        snippet: str = re.sub(r"<[^>]+>", "", snippet_raw).strip()
        snippet = re.sub(r"\s+", " ", snippet)
        
        results.append({"title": title, "url": url, "snippet": snippet})

    return results


def _brave_search(query: str, api_key: str) -> List[Dict[str, str]]:
    """
    Realiza una consulta a la API oficial de Brave Search (ideal para cuotas de nivel gratuito).

    Parámetros:
        query (str): Término o frase de búsqueda.
        api_key (str): Clave de API válida de Brave Search.

    Retorna:
        List[Dict[str, str]]: Lista de diccionarios con 'title', 'url' y 'snippet'.
    """
    url: str = f"{BRAVE_URL}?q={urllib.parse.quote(query)}&count={MAX_RES}"
    req = urllib.request.Request(url, headers={
        "Accept":              "application/json",
        "X-Subscription-Token": api_key,
    })
    try:
        # Timeout a 10 segundos para asegurar tolerancia
        with urllib.request.urlopen(req, timeout=10) as r:
            data: Dict[str, Any] = json.loads(r.read().decode("utf-8", errors="ignore"))
        
        results: List[Dict[str, str]] = []
        web_results: List[Dict[str, Any]] = data.get("web", {}).get("results", [])
        
        for item in web_results[:MAX_RES]:
            results.append({
                "title":   item.get("title", ""),
                "url":     item.get("url", ""),
                "snippet": item.get("description", ""),
            })
        return results
    except Exception:
        # Fallback transparente y automático a DuckDuckGo en caso de fallo de API o límite de cuota excedido
        return _ddg_search(query)


class WebSearch(Tool):
    """
    Herramienta integrada de búsqueda en la web.
    Usa de forma jerárquica Brave Search API (si existe clave) y DuckDuckGo HTML como fallback,
    entregando contexto enriquecido al modelo de lenguaje en formato Markdown estructurado.
    """
    name: str = "web_search"
    description: str = "Busca información actualizada en la web y la retorna estructurada."

    def execute(self, query: str, **kwargs: Any) -> ToolResult:
        """
        Punto de entrada para la ejecución de búsquedas web.

        Parámetros:
            query (str): Consulta de búsqueda.
            **kwargs: Parámetros opcionales adicionales.

        Retorna:
            ToolResult: Resultados web formateados en Markdown.
        """
        # Intentar obtener llave de Brave desde el KeyManager global
        try:
            from core.key_manager import KeyManager
            brave_key: Optional[str] = KeyManager.get_key("brave_search")
        except ImportError:
            brave_key = None

        if brave_key:
            results: List[Dict[str, str]] = _brave_search(query, brave_key)
        else:
            results = _ddg_search(query)

        if not results:
            return ToolResult(success=False, stderr="No se pudieron recuperar resultados de búsqueda web.")

        lines: List[str] = [f"**Resultados de búsqueda para:** `{query}`\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. **{r['title']}**")
            if r.get("url"):
                lines.append(f"   URL: {r['url']}")
            if r.get("snippet"):
                lines.append(f"   {r['snippet']}")
            lines.append("")

        return ToolResult(success=True, stdout="\n".join(lines), language="markdown")

