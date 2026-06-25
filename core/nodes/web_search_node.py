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

        query: str = inputs.get("query", "")
        max_results: int = int(inputs.get("max_results") or self.config.get("max_results") or 2)

        log.info(f"[WebSearchNode] Buscando: '{query}' (max={max_results})")

        result_text = search_and_scrape(query=query, max_results=max_results)

        return {
            "text": result_text,
            "found": bool(result_text and len(result_text) > 50),
        }
