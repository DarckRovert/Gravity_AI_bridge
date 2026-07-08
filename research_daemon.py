"""
GRAVITY AI — RESEARCH DAEMON (Modo Investigador)
Minero de datos autónomo para nutrir la base de conocimientos.
"""

import os
import sys
import time
import json
import threading
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from core.logger import log
from core import provider_manager
from core.firecrawl_scraper import scrape_url

class ResearchDaemon:
    def __init__(self, interval_hours=12):
        self.interval = interval_hours * 3600
        self.running = False
        self._thread = None
        self.knowledge_file = os.path.join(BASE_DIR, "_knowledge.json")
        self.context_file = os.path.join(BASE_DIR, "inputs", "investigador_context.txt")
        
        os.makedirs(os.path.dirname(self.context_file), exist_ok=True)

    def _get_target_topics(self):
        # Seleccionar temas de minería basados en el conocimiento actual o configuraciones
        return [
            "Avances recientes en neurociencia y conectomas",
            "Filosofía de la tecnología y ciberpolítica",
            "Física cuántica e inteligencia artificial"
        ]

    def _mine_topic(self, topic: str) -> str:
        """Utiliza el LLM para buscar y resumir información del tópico."""
        try:
            bp, bm = provider_manager.get_best()
            if not bp:
                return f"No hay proveedor LLM disponible para investigar: {topic}"

            prompt = (
                f"Eres el Investigador de Nexo Ágora. Elabora un reporte profundo y conciso "
                f"sobre los últimos avances o estado del arte en: '{topic}'. "
                f"Usa un tono académico y cyberpunk."
            )
            
            messages = [{"role": "user", "content": prompt}]
            
            log.info(f"[Investigador] Analizando: {topic} con {bp.name}/{bm}")
            result = provider_manager.complete(
                messages, model=bm, provider=bp.name, 
                options={"temperature": 0.4, "max_tokens": 800}
            )
            
            return result or "Error: Resultado vacío."
            
        except Exception as e:
            log.error(f"[Investigador] Error minando {topic}: {e}")
            return f"Error minando datos para {topic}."

    def loop(self):
        log.info("[JARVIS-Investigador] Iniciando ciclo de minería profunda.")
        while self.running:
            try:
                topics = self._get_target_topics()
                context_pills = []
                
                for t in topics:
                    res = self._mine_topic(t)
                    context_pills.append(f"### TEMA: {t}\n{res}\n")
                    time.sleep(10) # Pause between queries
                    
                full_context = "\n".join(context_pills)
                
                # Persistir contexto fresco
                with open(self.context_file, "w", encoding="utf-8") as f:
                    f.write(full_context)
                    
                log.info("[JARVIS-Investigador] Contexto actualizado exitosamente.")
                
            except Exception as e:
                log.error(f"[JARVIS-Investigador] Error en ciclo: {e}")
                
            # Dormir hasta el siguiente ciclo
            for _ in range(int(self.interval)):
                if not self.running:
                    break
                time.sleep(1)

    def start(self):
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self.loop, daemon=True, name="ResearchDaemon")
            self._thread.start()

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)

if __name__ == "__main__":
    daemon = ResearchDaemon(interval_hours=12) # Cada 12h
    daemon.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        daemon.stop()
