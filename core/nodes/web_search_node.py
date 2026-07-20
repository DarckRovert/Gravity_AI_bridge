"""
Gravity Workflow Node: WebSearch
Realiza búsqueda web en DuckDuckGo y retorna texto enriquecido.
"""

from core.workflow_engine import GravityNode, registry
from core.logger import log


@registry.register
class WebSearchNode(GravityNode):
    NODE_TYPE = "WebSearch"
    DESCRIPTION = "Busca en DuckDuckGo y scrapea los resultados principales."
    INPUT_SCHEMA = {
        "query": "TEXT",
        "max_results": "INT",  # default 2
    }
    OUTPUT_SCHEMA = {
        "text": "TEXT",
        "found": "BOOL",
    }

    def execute(self, inputs: dict) -> dict:
        from core.web_search import search_and_scrape

        import re
        query: str = inputs.get("query", "")
        # Remove quotes and trailing publisher (e.g., ' - La República')
        clean_query = query.replace('"', '').replace("'", "")
        # REQUIRE spaces around the hyphen to avoid breaking names like "Byung-Chul"
        clean_query = re.sub(r'\s+-\s+[^-\n]+$', '', clean_query)
        max_results: int = int(inputs.get("max_results") or self.config.get("max_results") or 2)

        log.info(f"[WebSearchNode] Buscando: '{clean_query}' (original: '{query}')")

        result_text = search_and_scrape(query=clean_query, max_results=max_results)

        # Fallback: Si no encontró nada, buscar solo las primeras 6 palabras
        if not result_text or len(result_text) < 50:
            words = clean_query.split()
            if len(words) > 6:
                short_query = " ".join(words[:6])
                log.info(f"[WebSearchNode] Fallback: Buscando titular acortado: '{short_query}'")
                result_text = search_and_scrape(query=short_query, max_results=max_results)

        return {
            "text": result_text,
            "found": bool(result_text and len(result_text) > 50),
        }
