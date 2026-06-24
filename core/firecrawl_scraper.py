"""
Gravity AI — Firecrawl Scraper V16.0 PRO
Scraping de URLs con soporte para API Firecrawl y fallback HTTP nativo.
Garantiza robustez multihilo, reintentos exponenciales y consumo seguro de configuración.
"""

import json
import time
import urllib.request
import urllib.parse
import html
import re
import socket
from typing import Optional, Dict, Any

from core.logger import log

BASE_URL: str = "https://api.firecrawl.dev/v1"


def _html_to_text(raw_html: str) -> str:
    """
    Extrae texto plano de HTML de forma defensiva y sin dependencias externas.
    Remueve scripts, estilos y etiquetas HTML, retornando un string limpio.
    """
    if not raw_html:
        return ""
    try:
        # Remover contenido de script y style
        text = re.sub(
            r"<script[^>]*>[\s\S]*?</script>", " ", raw_html, flags=re.IGNORECASE
        )
        text = re.sub(r"<style[^>]*>[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
        # Remover etiquetas HTML
        text = re.sub(r"<[^>]+>", " ", text)
        # Decodificar entidades HTML
        text = html.unescape(text)
        # Colapsar espacios redundantes
        text = re.sub(r"\s{3,}", "\n\n", text)
        return text.strip()[:8000]
    except Exception as e:
        log.warning(f"[Scraper] Error sanitizing HTML text: {e}")
        return raw_html.strip()[:8000]


def _request_with_retry(
    req: urllib.request.Request, timeout: int = 20, max_retries: int = 3
) -> urllib.request.urlopen:
    """
    Realiza una petición de red con reintentos exponenciales y manejo defensivo.
    Inmune a interrupciones esporádicas en flujos concurrentes pesados.
    """
    last_error: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except (urllib.error.URLError, socket.timeout) as e:
            last_error = e
            wait_time = 1.5 * (2**attempt)
            log.warning(
                f"[Scraper] Network delay/error on attempt {attempt + 1}/{max_retries}: {e}. "
                f"Retrying in {wait_time:.2f}s..."
            )
            time.sleep(wait_time)
        except Exception as e:
            # Errores HTTP severos (404, 401, etc.) o inesperados no se reintentan directamente
            log.error(f"[Scraper] Non-retryable network error: {e}")
            raise e
    if last_error:
        raise last_error
    raise urllib.error.URLError("Max retries exceeded without connection")


def scrape_url(url: str, api_key: str = "") -> Dict[str, Any]:
    """
    Realiza scraping de una URL de forma thread-safe y portable.

    - Si se especifica api_key o existe en ConfigManager: usa la API de Firecrawl (Markdown).
    - En caso contrario, o ante fallos de la API externa: aplica fallback nativo de HTML.

    Args:
        url: Dirección web a raspar. Debe comenzar con http:// o https://.
        api_key: Token opcional de la API de Firecrawl. Si se omite, se consulta en ConfigManager.

    Returns:
        Diccionario detallado con el estado, título, contenido y fuente del scraping.
    """
    if not url or not url.startswith(("http://", "https://")):
        return {
            "ok": False,
            "error": "URL inválida. Debe comenzar con http:// o https://",
            "url": url,
        }

    # Resolver API key: KeyManager (cifrado) > parámetro directo > fallback vacío
    resolved_api_key = api_key
    if not resolved_api_key:
        try:
            from core.key_manager import KeyManager

            resolved_api_key = KeyManager.get_key("firecrawl") or ""
        except Exception:
            resolved_api_key = ""

    if resolved_api_key:
        res = _scrape_via_firecrawl(url, resolved_api_key)
        if res.get("ok"):
            return res
        log.warning(
            f"[Scraper] Firecrawl API failed for {url}. Applying fallback scraping..."
        )

    return _scrape_via_fallback(url)


def _scrape_via_firecrawl(url: str, api_key: str) -> Dict[str, Any]:
    """Llama a la API de Firecrawl con reintentos para extraer markdown estructurado."""
    endpoint = f"{BASE_URL}/scrape"
    payload = json.dumps(
        {
            "url": url,
            "formats": ["markdown"],
            "onlyMainContent": True,
        }
    ).encode("utf-8")

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
        with _request_with_retry(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        content = data.get("data", {}).get("markdown", "") or data.get("data", {}).get(
            "content", ""
        )
        title = data.get("data", {}).get("metadata", {}).get("title", "") or ""

        return {
            "ok": True,
            "url": url,
            "title": title.strip(),
            "content": content[:8000].strip(),
            "source": "firecrawl",
        }
    except Exception as e:
        return {"ok": False, "error": f"Firecrawl API error: {e}", "url": url}


def _scrape_via_fallback(url: str) -> Dict[str, Any]:
    """Fallback thread-safe: descarga HTML y extrae texto plano con decodificación resiliente."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "GravityAI-Scraper/15.1 (compatible; Mozilla/5.0; Windows NT 10.0; Win64; x64)"
        },
    )
    try:
        with _request_with_retry(req, timeout=20) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            raw_html = resp.read().decode(charset, errors="replace")

        # Extraer título defensivamente
        title_match = re.search(
            r"<title[^>]*>(.*?)</title>", raw_html, re.IGNORECASE | re.DOTALL
        )
        title = html.unescape(title_match.group(1)).strip() if title_match else ""

        content = _html_to_text(raw_html)
        return {
            "ok": True,
            "url": url,
            "title": title,
            "content": content,
            "source": "fallback_html",
        }
    except Exception as e:
        return {"ok": False, "error": f"Fallback scrape error: {e}", "url": url}
