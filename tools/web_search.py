"""
Gravity AI — Web Search Tool V7.1
Sin API key requerida. Usa DuckDuckGo HTML scraping.
Opcional: Brave Search API (gratuita, 2000 req/mes).
"""
import re
import urllib.request
import urllib.parse
from tools.base_tool import Tool, ToolResult
from key_manager import KeyManager

DDG_URL   = "https://html.duckduckgo.com/html/"
BRAVE_URL = "https://api.search.brave.com/res/v1/web/search"
MAX_RES   = 5


def _ddg_search(query: str) -> list[dict]:
    """DuckDuckGo HTML scrape — no API key required."""
    data = urllib.parse.urlencode({"q": query, "kl": "es-es"}).encode()
    req  = urllib.request.Request(DDG_URL, data=data, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GravityAI/7.1",
        "Content-Type": "application/x-www-form-urlencoded",
    })
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            html = r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return [{"title": "Error", "url": "", "snippet": str(e)}]

    results = []
    # Parse result titles and snippets with regex (no BS4 required)
    titles   = re.findall(r'class="result__title"[^>]*>.*?<a[^>]*>(.*?)</a>', html, re.DOTALL)
    urls     = re.findall(r'class="result__url"[^>]*>\s*(.*?)\s*</a>', html, re.DOTALL)
    snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</span>', html, re.DOTALL)

    for i in range(min(MAX_RES, len(titles))):
        title   = re.sub(r"<[^>]+>", "", titles[i]).strip()
        url     = urls[i].strip() if i < len(urls) else ""
        snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip() if i < len(snippets) else ""
        results.append({"title": title, "url": url, "snippet": snippet})

    return results


def _brave_search(query: str, api_key: str) -> list[dict]:
    """Brave Search API (2000 free req/month)."""
    url  = f"{BRAVE_URL}?q={urllib.parse.quote(query)}&count={MAX_RES}"
    req  = urllib.request.Request(url, headers={
        "Accept":              "application/json",
        "Accept-Encoding":     "gzip",
        "X-Subscription-Token": api_key,
    })
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            import json
            data = json.loads(r.read().decode())
        results = []
        for item in data.get("web", {}).get("results", [])[:MAX_RES]:
            results.append({
                "title":   item.get("title", ""),
                "url":     item.get("url", ""),
                "snippet": item.get("description", ""),
            })
        return results
    except Exception as e:
        return _ddg_search(query)  # Fallback to DDG


class WebSearch(Tool):
    name        = "web_search"
    description = "Searches the web and returns top results as context"

    def execute(self, query: str, **kwargs) -> ToolResult:
        brave_key = KeyManager.get_key("brave_search")
        if brave_key:
            results = _brave_search(query, brave_key)
        else:
            results = _ddg_search(query)

        if not results:
            return ToolResult(success=False, stderr="No se encontraron resultados.")

        lines = [f"**Resultados de búsqueda para:** `{query}`\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. **{r['title']}**")
            if r.get("url"):
                lines.append(f"   URL: {r['url']}")
            if r.get("snippet"):
                lines.append(f"   {r['snippet']}")
            lines.append("")

        return ToolResult(success=True, stdout="\n".join(lines), language="markdown")
