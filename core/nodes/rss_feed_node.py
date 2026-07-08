import random
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, Any, List

from core.workflow_engine import GravityNode, registry
from core.logger import log

# 30 titulares de contingencia distribuidos por categorías del Lore
# Se usan cuando todos los feeds RSS fallan. La variedad previene repetición.
_CONTINGENCY_HEADLINES: List[str] = [
    # Vigilancia y control biométrico
    "El control biométrico global avanza mientras los gobiernos normalizan la vigilancia masiva",
    "Nuevas leyes de ciberespacio amenazan la soberanía digital de los ciudadanos",
    "Chinas social credit system inspira legislación en democracias occidentales",
    "El reconocimiento facial en aeropuertos: comodidad o puerta de entrada al panóptico total",
    "Implantes subdérmicos voluntarios: la nueva frontera del control biopolítico",
    # IA y tecnología
    "La inteligencia artificial y el dilema del control: ¿quién vigila al vigilante?",
    "Modelos de lenguaje bajo regulación estatal: el fin de la IA libre",
    "Deepfakes y la guerra de la realidad: cuando ver ya no es creer",
    "IA en los tribunales: algoritmos que dictan sentencia sin apelación humana",
    "El colapso de la privacidad digital: cómo los metadatos revelan más que el contenido",
    # Finanzas y cripto
    "Tokenización del mundo real: el Leviatán financiero expande su alcance",
    "Las monedas digitales de banco central y el fin del dinero anónimo",
    "El FMI presiona a naciones para adoptar marcos de vigilancia financiera global",
    "Bitcoin como resistencia: por qué los Estados temen la descentralización monetaria",
    "El colapso del dólar y la arquitectura del nuevo orden financiero multipolar",
    # Geopolítica
    "Resistencia digital: cómo las redes descentralizadas desafían al poder centralizado",
    "El nuevo mapa del poder: quién controla los cables submarinos controla el mundo",
    "Sanciones económicas como arma de guerra: el caso de las naciones que desafían al Leviatán",
    "La carrera por los minerales críticos: el nuevo recurso que define el siglo XXI",
    "Geopolítica del agua: los próximos conflictos se librarán por el recurso más escaso",
    # Salud y bioética
    "Salud digital y el precio de la conveniencia: tus datos médicos como mercancía",
    "Edición genética y desigualdad: CRISPR para ricos, enfermedad para pobres",
    "La pandemia como laboratorio del control social: lecciones que el poder no olvidará",
    "Neurotecnología invasiva: el próximo frente de batalla de la soberanía individual",
    "Patentes farmacéuticas versus acceso global: la bioética en tiempos del Leviatán",
    # Psicología y control social
    "Algoritmos de adicción: cómo las plataformas capturan la voluntad humana",
    "La economía de la atención y la ingeniería del consenso masivo",
    "Desinformación institucional: cuando el Estado es el mayor productor de fake news",
    "El individuo anestesiado: cómo el consumismo silencia la resistencia política",
    "Psicopolítica y big data: Byung-Chul Han tenía razón sobre el nuevo poder",
]

@registry.register
class RSSFeedNode(GravityNode):
    NODE_TYPE = "RSSFeed"
    DESCRIPTION = "Lee un feed RSS/XML y extrae un titular. Soporta múltiples URLs, feeds Atom, y deduplicación editorial."
    INPUT_SCHEMA = {
        "url": "TEXT",          # Una o múltiples URLs separadas por coma
        "max_items": "INT",     # De los primeros X items, escoge 1
        "deduplicate": "BOOL",  # Si True, evita titulares ya publicados (default True)
    }
    OUTPUT_SCHEMA = {
        "headline": "TEXT",
        "source_url": "TEXT",
        "is_contingency": "BOOL",
    }

    # Namespace Atom para parsear feeds modernos
    _ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}

    def _fetch_candidates(self, url: str, max_items: int) -> List[str]:
        """
        Obtiene hasta max_items titulares de un feed RSS o Atom.
        Retorna lista de strings (puede estar vacía).
        """
        req = urllib.request.Request(
            url.strip(),
            headers={"User-Agent": "Mozilla/5.0 (Gravity AI Editorial Bot)"},
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)
        candidates: List[str] = []

        # RSS 2.0
        items = root.findall(".//item")
        for item in items[:max_items]:
            title_el = item.find("title")
            if title_el is not None and title_el.text and title_el.text.strip():
                candidates.append(title_el.text.strip())

        # Atom feed (si no se encontraron items RSS)
        if not candidates:
            entries = root.findall("atom:entry", self._ATOM_NS)
            if not entries:  # Atom sin namespace explícito
                entries = root.findall(".//entry")
            for entry in entries[:max_items]:
                title_el = entry.find("atom:title", self._ATOM_NS)
                if title_el is None:
                    title_el = entry.find("title")
                if title_el is not None and title_el.text and title_el.text.strip():
                    candidates.append(title_el.text.strip())

        return candidates

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        url_input = inputs.get("url", "")
        max_items = int(inputs.get("max_items", 5))
        deduplicate = inputs.get("deduplicate", True)
        if isinstance(deduplicate, str):
            deduplicate = deduplicate.lower() not in ("false", "0", "no")

        if not url_input:
            raise ValueError(f"[{self.node_id}] URL de RSS no especificada.")

        urls: List[str] = [u.strip() for u in url_input.split(",") if u.strip()]
        random.shuffle(urls)  # Rotar fuentes para diversidad

        # Cargar funciones de memoria editorial para deduplicación
        _seen_fn = None
        _record_fn = None
        if deduplicate:
            try:
                from core.editorial_memory import seen_headline as _seen_fn, record_headline as _record_fn
            except Exception:
                pass

        feeds_with_candidates = 0
        feeds_failed = 0
        chosen_headline = ""
        chosen_url = ""

        for url in urls:
            try:
                candidates = self._fetch_candidates(url, max_items)
                if not candidates:
                    log.warning(f"[{self.__class__.__name__}] Sin titulares en: {url}")
                    feeds_failed += 1
                    continue

                feeds_with_candidates += 1
                random.shuffle(candidates)

                for candidate in candidates:
                    if _seen_fn and _seen_fn(candidate, window_days=7):
                        log.info(f"[{self.__class__.__name__}] Titular duplicado, saltando: '{candidate[:50]}'")
                        continue
                    chosen_headline = candidate
                    chosen_url = url
                    break

                if chosen_headline:
                    break
                log.info(f"[{self.__class__.__name__}] Todos los titulares de {url} son duplicados. Siguiente feed.")

            except Exception as e:
                log.warning(f"[{self.__class__.__name__}] Falló RSS {url}: {e}")
                feeds_failed += 1

        log.info(
            f"[{self.__class__.__name__}] RSS: {feeds_with_candidates} feeds con candidatos, "
            f"{feeds_failed} fallidos, titular={'encontrado' if chosen_headline else 'NO encontrado'}."
        )

        if chosen_headline:
            # BUG-2 FIX: registrar el titular RSS crudo aquí mismo, donde el string original está disponible
            if _record_fn:
                try:
                    _record_fn(chosen_headline, source=chosen_url, workflow="reporter")
                except Exception:
                    pass
            log.info(f"[{self.__class__.__name__}] Titular seleccionado: {chosen_headline}")
            return {"headline": chosen_headline, "source_url": chosen_url, "is_contingency": False}

        # Contingencia: elegir de la lista local evitando duplicados si es posible
        pool = list(_CONTINGENCY_HEADLINES)
        random.shuffle(pool)
        for fallback in pool:
            if _seen_fn and _seen_fn(fallback, window_days=3):
                continue
            chosen_headline = fallback
            break
        if not chosen_headline:
            chosen_headline = random.choice(_CONTINGENCY_HEADLINES)

        log.warning(
            f"[{self.__class__.__name__}] Usando titular de contingencia: {chosen_headline}"
        )
        return {"headline": chosen_headline, "source_url": "contingency", "is_contingency": True}

