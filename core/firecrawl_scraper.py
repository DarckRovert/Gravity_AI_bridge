"""
Gravity AI — Firecrawl Scraper V13.0 PRO
Scraping de URLs con soporte para API Firecrawl y fallback HTTP nativo.
Si firecrawl_api_key está vacío, usa urllib como fallback.
"""
import json
import time
import urllib.request
import urllib.parse
import html
import re
from typing import Optional, Dict, Any

BASE_URL = "https://api.firecrawl.dev/v1"


def _html_to_text(raw_html: str) -> str:
    """Fallback: extrae texto plano de HTML sin dependencias externas."""
    text = re.sub(r"<script[^>]*>[\s\S]*?</script>", " ", raw_html, flags=re.IGNORECASE)
    text = re.sub(r"<style[^>]*>[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s{3,}", "\n\n", text)
    return text.strip()[:8000]


def scrape_url(url: str, api_key: str = "") -> Dict[str, Any]:
    """
    Scraping de una URL.
    - Si api_key provisto: usa Firecrawl API (resultado Markdown limpio).
    - Si no: usa urllib como fallback (texto plano desde HTML).
    """
    if not url or not url.startswith(("http://", "https://")):
        return {"ok": False, "error": "URL inválida. Debe comenzar con http:// o https://"}

    if api_key:
        res = _scrape_via_firecrawl(url, api_key)
        if res.get("ok"):
            return res
        # Fallback if Firecrawl fails
        return _scrape_via_fallback(url)
    return _scrape_via_fallback(url)


def _scrape_via_firecrawl(url: str, api_key: str) -> Dict[str, Any]:
    """Llama a la API de Firecrawl para extraer markdown limpio."""
    endpoint = f"{BASE_URL}/scrape"
    payload = json.dumps({
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": True,
    }).encode("utf-8")

    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data.get("data", {}).get("markdown", "") or data.get("data", {}).get("content", "")
        title   = data.get("data", {}).get("metadata", {}).get("title", "")
        return {
            "ok":      True,
            "url":     url,
            "title":   title,
            "content": content[:8000],
            "source":  "firecrawl",
        }
    except Exception as e:
        return {"ok": False, "error": f"Firecrawl API error: {str(e)}", "url": url}


def _scrape_via_fallback(url: str) -> Dict[str, Any]:
    """Fallback: descarga HTML y extrae texto plano."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "GravityAI-Scraper/10.4 (compatible; Mozilla/5.0)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            charset  = resp.headers.get_content_charset() or "utf-8"
            raw_html = resp.read().decode(charset, errors="replace")

        title_match = re.search(r"<title[^>]*>(.*?)</title>", raw_html, re.IGNORECASE | re.DOTALL)
        title = html.unescape(title_match.group(1)).strip() if title_match else ""

        content = _html_to_text(raw_html)
        return {
            "ok":      True,
            "url":     url,
            "title":   title,
            "content": content,
            "source":  "fallback_html",
        }
    except Exception as e:
        return {"ok": False, "error": f"Fallback scrape error: {str(e)}", "url": url}
