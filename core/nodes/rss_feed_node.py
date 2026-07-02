import random
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, Any, List

from core.workflow_engine import GravityNode, registry
from core.logger import log

_CONTINGENCY_HEADLINES = [
    "El control biométrico global avanza mientras los gobiernos normalizan la vigilancia masiva",
    "Nuevas leyes de ciberespacio amenazan la soberanía digital de los ciudadanos",
    "La inteligencia artificial y el dilema del control: ¿quién vigila al vigilante?",
    "Tokenización del mundo real: el Leviatán financiero expande su alcance",
    "Resistencia digital: cómo las redes descentralizadas desafían al poder centralizado",
]

@registry.register
class RSSFeedNode(GravityNode):
    NODE_TYPE = "RSSFeed"
    DESCRIPTION = "Lee un feed RSS/XML y extrae un titular. Soporta múltiples URLs como fallback."
    INPUT_SCHEMA = {
        "url": "TEXT",          # Una o múltiples URLs separadas por coma
        "max_items": "INT"      # De los primeros X items, escoge 1
    }
    OUTPUT_SCHEMA = {
        "headline": "TEXT"
    }

    def _fetch_headline(self, url: str, max_items: int) -> str:
        """Intenta obtener un titular de una URL RSS. Retorna str o lanza excepción."""
        req = urllib.request.Request(url.strip(), headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        items = root.findall(".//item")
        if not items:
            raise ValueError(f"No se encontraron <item> en el XML de {url}")
        top_items = items[:max_items]
        chosen = random.choice(top_items)
        title_el = chosen.find("title")
        if title_el is None or not title_el.text:
            raise ValueError(f"Titular vacío en {url}")
        return title_el.text.strip()

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        url_input = inputs.get("url", "")
        max_items = int(inputs.get("max_items", 5))

        if not url_input:
            raise ValueError(f"[{self.node_id}] URL de RSS no especificada.")

        urls: List[str] = [u.strip() for u in url_input.split(",") if u.strip()]
        random.shuffle(urls)  # Rotar fuentes para diversidad

        last_error = None
        for url in urls:
            try:
                log.info(f"[{self.__class__.__name__}] Escaneando RSS: {url}")
                headline = self._fetch_headline(url, max_items)
                log.info(f"[{self.__class__.__name__}] Titular seleccionado: {headline}")
                return {"headline": headline}
            except Exception as e:
                log.warning(f"[{self.__class__.__name__}] Falló RSS {url}: {e}. Intentando siguiente...")
                last_error = e

        # Todas las fuentes fallaron — contingencia en lugar de abortar
        contingency = random.choice(_CONTINGENCY_HEADLINES)
        log.warning(
            f"[{self.__class__.__name__}] Todas las fuentes RSS fallaron ({last_error}). "
            f"Usando titular de contingencia: {contingency}"
        )
        return {"headline": contingency}

