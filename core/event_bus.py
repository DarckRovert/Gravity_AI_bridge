"""
Gravity AI — Real-time In-Process Event Bus V1.0 PRO (Mythos Edition)

Bus de eventos in-process basado en Pub/Sub para Server-Sent Events (SSE),
desacoplando notificaciones en tiempo real sin sobrecarga de WebSockets.
"""

import queue
import time
import threading
from typing import Dict, Set, Generator, Any, Optional
from core.logger import log


class EventBus:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._setup()
                cls._instance = inst
        return cls._instance

    def _setup(self):
        self._listeners: Dict[str, Set[queue.Queue]] = {}
        self._listeners_lock = threading.Lock()

    def publish(self, topic: str, event_type: str, data: Any):
        """Publica un evento en un tópico determinado."""
        with self._listeners_lock:
            subscribers = set(self._listeners.get(topic, set()))

        if not subscribers:
            return

        payload = {
            "event": event_type,
            "data": data,
            "timestamp": time.time(),
        }

        for q in subscribers:
            try:
                q.put_nowait(payload)
            except queue.Full:
                log.warning(f"[EventBus] Cola llena para suscriptor en tópico '{topic}'")

    def subscribe(self, topic: str) -> Generator[Dict[str, Any], None, None]:
        """Generador SSE que produce eventos para un suscriptor en streaming."""
        q = queue.Queue(maxsize=100)

        with self._listeners_lock:
            if topic not in self._listeners:
                self._listeners[topic] = set()
            self._listeners[topic].add(q)

        log.debug(f"[EventBus] Nuevo suscriptor conectado al tópico '{topic}'")

        try:
            while True:
                try:
                    # Espera con timeout para enviar pings de heartbeat
                    item = q.get(timeout=20.0)
                    yield item
                except queue.Empty:
                    # Heartbeat SSE para mantener la conexión viva y evitar anti-buffering de proxies
                    yield {"event": "ping", "data": {"time": time.time()}}
        finally:
            with self._listeners_lock:
                if topic in self._listeners:
                    self._listeners[topic].discard(q)
                    if not self._listeners[topic]:
                        del self._listeners[topic]
            log.debug(f"[EventBus] Suscriptor desconectado del tópico '{topic}'")


# Singleton global
event_bus = EventBus()
