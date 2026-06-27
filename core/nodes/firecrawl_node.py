from typing import Dict, Any

from core.workflow_engine import GravityNode, registry
from core.logger import log

@registry.register

class FirecrawlNode(GravityNode):
    """
    Realiza un scraping profundo de una URL convirtiéndola en Markdown.
    Inputs requeridos:
      - url: URL a extraer.
    Inputs opcionales:
      - mode: "scrape" o "crawl" (default: "scrape")
    """
    
    NODE_TYPE = "Firecrawl"
    DESCRIPTION = "Realiza un scraping profundo de una URL convirtiéndola en Markdown."
    INPUT_SCHEMA = {
        "url": "TEXT",
        "mode": "TEXT"
    }
    OUTPUT_SCHEMA = {
        "markdown": "TEXT",
        "metadata": "JSON"
    }
    


    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        url = inputs.get("url")
        mode = inputs.get("mode", "scrape")

        if not url:
            raise ValueError(f"[{self.node_id}] URL no especificada.")

        from core.firecrawl_scraper import scrape_url
        
        log.info(f"[{self.__class__.__name__}] Extrayendo URL: {url} (modo={mode})")
        
        try:
            # We assume scrape_url handles both API and fallback
            # and returns a dictionary with 'content' as markdown
            result = scrape_url(url)
            markdown_content = result.get("content", "")
            
            if not markdown_content:
                raise RuntimeError(f"[{self.node_id}] Resultado vacío para URL {url}")
                
            return {"markdown": markdown_content, "metadata": result.get("metadata", {})}
        except Exception as e:
            log.error(f"[{self.__class__.__name__}] Error en Firecrawl: {e}")
            raise
