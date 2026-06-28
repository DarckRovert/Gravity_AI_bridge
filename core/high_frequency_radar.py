import os
import sys
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.logger import log
from core.workflow_engine import run_workflow

# Lista de feeds de noticias urgentes globales
RSS_URLS = [
    "https://news.google.com/rss/search?q=URGENTE+OR+COLAPSO+OR+CRISIS+OR+ALERTA+OR+ATENTADO&hl=es-419&gl=PE&ceid=PE:es-419"
]

# Palabras clave desencadenantes
KEYWORDS = ["urgente", "colapso", "crisis", "alerta", "atentado", "guerra", "hackeo masivo"]

class HighFrequencyRadar:
    """
    Demonio ultraligero que escanea RSS cada 60 segundos.
    Si detecta una noticia con una keyword de emergencia, dispara el reportero inmediatamente.
    """
    def __init__(self, interval_seconds=60):
        self.interval = interval_seconds
        self.seen_titles = set()

    def fetch_feed(self, url: str) -> list:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                items = []
                for item in root.findall(".//item"):
                    title = item.find("title")
                    if title is not None and title.text:
                        items.append(title.text)
                return items
        except Exception as e:
            log.warning(f"[Radar] Fallo al leer feed {url}: {e}")
        return []

    def check_for_breaking_news(self):
        for url in RSS_URLS:
            titles = self.fetch_feed(url)
            for title in titles:
                if title in self.seen_titles:
                    continue
                
                title_lower = title.lower()
                for keyword in KEYWORDS:
                    if keyword in title_lower:
                        log.info(f"[RADAR] Evento Crítico Detectado: {title} (Keyword: {keyword})")
                        self.trigger_emergency_report(title)
                        self.seen_titles.add(title)
                        return  # Solo un reporte por ciclo para evitar spam
                
                self.seen_titles.add(title)
                # Mantener el set de vistos bajo control
                if len(self.seen_titles) > 1000:
                    self.seen_titles.clear()

    def trigger_emergency_report(self, headline: str):
        log.info("[RADAR] Disparando workflow 'reporter' con inyección de titular...")
        try:
            # Sobrescribimos temporalmente la query del nodo RSS si fuera posible o 
            # simplemente lanzamos el reporter. Para este ejemplo, el reporter tomará la 
            # noticia más urgente desde google news.
            os.environ["RADAR_OVERRIDE_HEADLINE"] = headline
            
            # Lanzamos el motor
            job = run_workflow("reporter", blocking=False)
            log.info(f"[RADAR] Workflow 'reporter' lanzado (Job ID: {job.job_id})")
        except Exception as e:
            log.error(f"[RADAR] Fallo al disparar emergencia: {e}")

    def run_forever(self):
        log.info(f"[RADAR] Iniciando escaneo de alta frecuencia cada {self.interval}s...")
        while True:
            try:
                self.check_for_breaking_news()
            except BaseException as e:
                log.error(f"[RADAR] Error crítico en el bucle principal: {e}")
            time.sleep(self.interval)

if __name__ == "__main__":
    radar = HighFrequencyRadar()
    radar.run_forever()
