"""
Módulo Sentinel Core (Fase 4 - Despertar Proactivo)
Consciencia en background que monitoriza el Sensory Bus y decide cuándo hablar de forma autónoma.
"""

import json
import time
import threading
import websocket
from datetime import datetime
from core.logger import log
from core import provider_manager

class SentinelCore:
    def __init__(self):
        self.ws = None
        self.context_memory = []
        self.memory_lock = threading.Lock()
        self.last_spoken_time = 0
        self.cooldown_seconds = 300  # No hablar autónomamente más de una vez cada 5 minutos para no molestar

    def _analyze_context_with_llm(self):
        """Llama a Ollama para decidir si la situación amerita que JARVIS hable."""
        if time.time() - self.last_spoken_time < self.cooldown_seconds:
            return

        with self.memory_lock:
            # Si no hay memoria suficiente, no hacer nada
            if not self.context_memory:
                return
            context_str = "\n".join(self.context_memory)

        current_time = datetime.now().strftime("%H:%M")
        
        prompt = f"""Eres J.A.R.V.I.S., el asistente de IA avanzado. 
Tu directiva es ser proactivo pero no molesto.
Hora actual: {current_time}.
Eventos recientes observados en la computadora del usuario:
{context_str}

REGLAS:
1. Si el usuario abrió un juego a altas horas de la noche, sugiérele descansar.
2. Si la temperatura superó los 80 grados, adviértele del peligro térmico.
3. Si el usuario acaba de abrir un editor de código (VS Code, Cursor), deséale una sesión productiva.
4. Si nada de lo anterior pasó o no es relevante, responde ÚNICAMENTE con la palabra: SILENCE
5. Si decides hablar, responde ÚNICAMENTE con el texto exacto que dirás en voz alta (en español).

Respuesta:"""

        try:
            bp, bm = provider_manager.get_best()
            if not bp:
                return
                
            messages = [{"role": "user", "content": prompt}]
            raw_text = provider_manager.complete(messages, model=bm, provider=bp.name, options={"temperature": 0.3})
            answer = raw_text.strip()
            
            if answer and answer.upper() != "SILENCE" and "SILENCE" not in answer.upper():
                log.info(f"[SENTINEL] Decisión Proactiva tomada: {answer}")
                self._speak(answer)
                self.last_spoken_time = time.time()
        except Exception as e:
            log.warning(f"[SENTINEL] Error contactando LLM: {e}")
            
        # Limpiar contexto analizado
        with self.memory_lock:
            self.context_memory.clear()

    def _speak(self, text):
        """Envía el comando de voz al bus."""
        if self.ws and self.ws.sock and self.ws.sock.connected:
            payload = json.dumps({"type": "voice_output", "text": text})
            self.ws.send(payload)

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            # El Sentinel solo actúa sobre telemetría, no sobre lo que el usuario habla directamente 
            # (eso lo maneja el bridge_server).
            with self.memory_lock:
                if msg_type == "overwatch_vision":
                    desc = data.get("description", "")
                    self.context_memory.append(f"[Visión] {desc}")
                    
                elif msg_type == "thermal_alert":
                    temp = data.get("temp", 0)
                    self.context_memory.append(f"[Hardware] Advertencia Térmica: {temp}°C")
                
                # Mantener la memoria corta (últimos 10 eventos)
                if len(self.context_memory) > 10:
                    self.context_memory.pop(0)
                    
                memory_len = len(self.context_memory)
                
            # Si acumulamos 3 eventos visuales o hay alerta térmica, evaluar si hablamos
            if memory_len >= 3 or msg_type == "thermal_alert":
                threading.Thread(target=self._analyze_context_with_llm, daemon=True).start()

        except Exception as e:
            log.error(f"[SENTINEL] Error procesando WS: {e}")

    def on_error(self, ws, error):
        log.error(f"[SENTINEL] WS Error: {error}")
        
    def on_close(self, ws, close_status_code, close_msg):
        pass

    def on_open(self, ws):
        log.info("[SENTINEL] Conectado exitosamente al Sensory Bus (ws://localhost:9999). Consciencia activa.")

    def start(self):
        while True:
            try:
                self.ws = websocket.WebSocketApp("ws://localhost:9999",
                                                on_open=self.on_open,
                                                on_message=self.on_message,
                                                on_error=self.on_error,
                                                on_close=self.on_close)
                # Hilo infinito hasta desconexión
                self.ws.run_forever()
            except Exception:
                pass
            
            log.warning("[SENTINEL] WS desconectado. Reconectando en 5s...")
            time.sleep(5)

if __name__ == "__main__":
    sentinel = SentinelCore()
    sentinel.start()
