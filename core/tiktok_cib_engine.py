"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — GTLIS CIB & BOTNET NETWORK GRAPH ENGINE V1.0                   ║
║  Detector de Comportamiento Inauténtico Coordinado en Tiempo Real            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import time
import threading
from collections import defaultdict, deque
from typing import Dict, Any, List, Set
from core.logger import log


class CIBNetworkEngine:
    """
    Analiza en tiempo real la red de usuarios que comentan en transmisiones en vivo.
    Detecta patrones de astroturfing, ataques de raid y granjas de bots organizadas.
    """
    def __init__(self) -> None:
        self._user_channels: Dict[str, Set[str]] = defaultdict(set)
        self._text_hashes: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._lock = threading.Lock()

    def _prune_stale_entries(self, now: float) -> None:
        """Purga entradas de más de 5 minutos (300 segundos) para liberar memoria y evitar sesgo temporal."""
        stale_keys = []
        for text, entries in self._text_hashes.items():
            valid_entries = [e for e in entries if now - e["ts"] < 300]
            if valid_entries:
                self._text_hashes[text] = valid_entries
            else:
                stale_keys.append(text)
        for key in stale_keys:
            del self._text_hashes[key]

    def record_comment(self, username: str, user_id: str, text: str) -> None:
        """Registra un comentario para análisis de coordinación cruzada."""
        if not user_id or not text or user_id == "anonymous":
            return
        
        now = time.time()
        clean_text = str(text).strip().lower()
        norm_username = str(username).lstrip("@").lower()
        
        with self._lock:
            self._prune_stale_entries(now)
            self._user_channels[user_id].add(norm_username)
            self._text_hashes[clean_text].append({
                "username": norm_username,
                "user_id": user_id,
                "ts": now
            })

    def get_cib_report(self, username: str) -> Dict[str, Any]:
        """Calcula el índice CIB y detecta patrones de coordinación inauténtica."""
        username = username.lstrip("@").lower()
        now = time.time()
        with self._lock:
            self._prune_stale_entries(now)
            cross_stream_bots = []
            for uid, channels in self._user_channels.items():
                if username in channels and len(channels) > 1:
                    cross_stream_bots.append({
                        "user_id": uid,
                        "shared_channels_count": len(channels),
                        "channels": list(channels)
                    })

            # Detectar frases coordinadas duplicadas enviadas por MÚLTIPLES cuentas distintas (Astroturfing)
            coordinated_phrases = []
            for text, entries in self._text_hashes.items():
                channel_entries = [e for e in entries if e["username"] == username]
                unique_senders = len(set(e["user_id"] for e in channel_entries))
                if len(channel_entries) >= 3 and unique_senders >= 2:
                    coordinated_phrases.append({
                        "phrase": text[:40],
                        "occurrences": len(channel_entries),
                        "unique_senders": unique_senders
                    })

            cib_score = min(1.0, round((len(cross_stream_bots) * 0.15) + (len(coordinated_phrases) * 0.2), 2))

            return {
                "username": username,
                "cib_score": cib_score,
                "is_coordinated_attack": cib_score > 0.4,
                "cross_stream_users_detected": len(cross_stream_bots),
                "coordinated_phrases_count": len(coordinated_phrases),
                "top_cross_users": cross_stream_bots[:10],
                "top_coordinated_phrases": coordinated_phrases[:5]
            }


_cib_engine_instance = CIBNetworkEngine()

def get_cib_engine() -> CIBNetworkEngine:
    return _cib_engine_instance
