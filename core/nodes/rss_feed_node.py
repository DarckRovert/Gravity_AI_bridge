import random
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, Any

from core.workflow_engine import GravityNode, registry
from core.logger import log

@registry.register
class RSSFeedNode(GravityNode):
    NODE_TYPE = "RSSFeed"
    DESCRIPTION = "Lee un feed RSS/XML y extrae un titular de manera aleatoria."
    INPUT_SCHEMA = {
        "url": "TEXT",          # Una sola URL o múltiples separadas por comas
        "max_items": "INT"      # De los primeros X items, escoge 1
    }
    OUTPUT_SCHEMA = {
        "headline": "TEXT"
    }

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        url_input = inputs.get("url", "")
        max_items = int(inputs.get("max_items", 5))

        if not url_input:
            raise ValueError(f"[{self.node_id}] URL de RSS no especificada.")

        urls = [u.strip() for u in url_input.split(",") if u.strip()]
        target_url = random.choice(urls)

        log.info(f"[{self.__class__.__name__}] Escaneando RSS: {target_url}")

        req = urllib.request.Request(target_url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                items = root.findall(".//item")
                if not items:
                    raise ValueError(f"No se encontraron <item> en el XML de {target_url}")
                
                top_items = items[:max_items]
                chosen = random.choice(top_items)
                title = chosen.find("title").text
                
                log.info(f"[{self.__class__.__name__}] Titular seleccionado: {title}")
                return {"headline": title}
        except Exception as e:
            log.error(f"[{self.__class__.__name__}] Error parseando RSS: {e}")
            raise
