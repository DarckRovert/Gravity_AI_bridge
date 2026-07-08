"""
Módulo Vigía: Detector de Anomalías Constante
Escanea iterativamente los logs y reporta advertencias preventivas.
"""

import time
import os
import sys
import threading
import json
from datetime import datetime, timezone
from typing import Dict, Any

# Ensure we can import 'core' even if run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger import log

class AnomalyWatchdog:
    def __init__(self, interval_seconds: int = 300):
        self.interval = interval_seconds
        self.running = False
        self._thread = None
        self.log_file = os.path.join(
            os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")), 
            "Gravity", 
            "Logs",
            "bridge.log"
        )
        
        self.app_data = os.path.join(
            os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")), 
            "Gravity", 
            "Databases"
        )
        self.state_file = os.path.join(self.app_data, "_vigia_state.json")

    def _calculate_entropy(self, text: str) -> float:
        """Calcula una pseudo-entropía basada en la variabilidad de caracteres y palabras."""
        if not text:
            return 0.0
        words = text.split()
        if len(words) == 0:
            return 0.0
        unique_words = set(words)
        return len(unique_words) / len(words)

    def analyze_news_quality(self) -> Dict[str, Any]:
        """Evalúa la calidad de la última publicación."""
        periodista_file = os.path.join(self.app_data, "_periodista_state.json")
        result = {"entropy": 1.0, "status": "NORMAL"}
        
        if not os.path.isfile(periodista_file):
            return result
            
        try:
            with open(periodista_file, "r", encoding="utf-8") as f:
                state = json.load(f)
                
            last_title = state.get("last_article_title", "")
            
            if last_title:
                entropy = self._calculate_entropy(last_title)
                result["entropy"] = round(entropy, 2)
                
                # Si el título es muy repetitivo (entropía baja) o siempre el mismo texto por defecto
                if entropy < 0.3 or last_title == "Transmisión Clandestina de la Zona Ágora":
                    result["status"] = "ALERTA_DEGRADACION_LLM"
                    
        except Exception as e:
            log.warning(f"[Watchdog] Error analizando calidad de noticias: {e}")
            
        return result

    def scan_logs(self) -> Dict[str, Any]:
        """Escanea las últimas líneas del log buscando patrones de error crítico."""
        if not os.path.isfile(self.log_file):
            return {"error_count": 0, "status": "NORMAL"}
            
        error_count = 0
        try:
            # Leer las últimas 500 líneas
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()[-500:]
                
            for line in lines:
                try:
                    data = json.loads(line)
                    if data.get("level") in ("ERROR", "CRITICAL"):
                        error_count += 1
                except Exception:
                    # Logs no-JSON, fallback básico
                    if "ERROR" in line or "CRITICAL" in line:
                        error_count += 1
                        
            status = "NORMAL"
            if error_count > 50:
                status = "CRITICAL_ERROR_SPIKE"
            elif error_count > 10:
                status = "WARNING_ERRORS"
                
            return {"error_count": error_count, "status": status}
            
        except Exception as e:
            log.warning(f"[Watchdog] Error escaneando logs: {e}")
            return {"error_count": -1, "status": "UNKNOWN"}

    def _save_state(self, state: dict):
        try:
            os.makedirs(self.app_data, exist_ok=True)
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            log.error(f"[Watchdog] No se pudo guardar estado: {e}")

    def loop(self):
        log.info("[JARVIS-Vigia] Iniciando escaneo continuo de anomalías.")
        while self.running:
            try:
                quality_res = self.analyze_news_quality()
                log_res = self.scan_logs()
                
                state = {
                    "last_scan_utc": datetime.now(timezone.utc).isoformat(),
                    "quality": quality_res,
                    "logs": log_res,
                    "overall_status": "NORMAL"
                }
                
                if quality_res["status"] != "NORMAL" or log_res["status"] not in ("NORMAL", "UNKNOWN"):
                    state["overall_status"] = "ALERTA"
                    log.warning(f"[JARVIS-Vigia] Anomalía detectada! Calidad: {quality_res['status']} | Logs: {log_res['status']}")
                
                self._save_state(state)
                
            except Exception as e:
                log.error(f"[JARVIS-Vigia] Error en loop: {e}")
                
            time.sleep(self.interval)

    def start(self):
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self.loop, daemon=True, name="AnomalyWatchdog")
            self._thread.start()

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)

if __name__ == "__main__":
    daemon = AnomalyWatchdog(interval_seconds=60)
    daemon.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        daemon.stop()
