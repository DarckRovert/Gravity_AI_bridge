import json
import os
import time
import threading
from datetime import datetime, timezone
from collections import deque

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_LINES = 10_000  # 10k líneas — umbral de rotación por volumen


class AuditLogger:
    """
    Immutable audit log for all inference calls (append-only JSONL).
    Records: timestamp, session_id, provider, model, tokens, latency, cost.
    V2: Rotación automática cuando el archivo supera MAX_BYTES (5 MB) o MAX_LINES (10k).
    V3: get_recent() optimizado con deque — no carga el archivo completo en memoria.
    V4: Concurrencia segura mediante un Lock para evitar colisiones al escribir/rotar en disco.
    """

    def __init__(self, log_path: str = "_audit_log.jsonl"):
        self._lock = threading.Lock()
        with self._lock:
            # Soportar rutas relativas y absolutas
            if not os.path.isabs(log_path):
                self.log_path = os.path.join(BASE_DIR, log_path)
            else:
                self.log_path = log_path
            self._line_count: int = self._count_lines_unlocked()

    def _count_lines_unlocked(self) -> int:
        """Cuenta líneas del log actual sin cargarlo en memoria (no thread-safe, debe llamarse con lock)."""
        if not os.path.isfile(self.log_path):
            return 0
        try:
            count = 0
            with open(self.log_path, "rb") as f:
                for _ in f:
                    count += 1
            return count
        except Exception:
            return 0

    def _count_lines(self) -> int:
        """Cuenta líneas del log actual sin cargarlo en memoria."""
        with self._lock:
            return self._count_lines_unlocked()

    def _rotate_if_needed(self) -> None:
        """Rota el log si supera MAX_BYTES o MAX_LINES (debe llamarse bajo self._lock)."""
        try:
            needs_rotation = False
            if os.path.isfile(self.log_path):
                if os.path.getsize(self.log_path) >= MAX_BYTES:
                    needs_rotation = True
                elif self._line_count >= MAX_LINES:
                    needs_rotation = True

            if needs_rotation:
                bak = self.log_path.replace(".jsonl", f".bak.{int(time.time())}.jsonl")
                os.rename(self.log_path, bak)
                self._line_count = 0
                # Mantener máximo 3 backups — eliminar los más viejos
                base_dir = os.path.dirname(self.log_path)
                base_name = os.path.basename(self.log_path).replace(".jsonl", "")
                baks = sorted(
                    [
                        f
                        for f in os.listdir(base_dir)
                        if f.startswith(base_name + ".bak.")
                    ]
                )
                while len(baks) > 3:
                    os.remove(os.path.join(base_dir, baks.pop(0)))
        except Exception:
            pass

    def record(
        self,
        session_id: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        latency_ms: float,
    ):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "session_id": session_id,
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "latency_ms": latency_ms,
            "cost_usd": cost_usd,
        }

        with self._lock:
            self._rotate_if_needed()

            try:
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")
                self._line_count += 1
            except Exception:
                pass  # Silencioso en frozen build — stdout puede no estar disponible

    def get_recent(self, limit: int = 50) -> list:
        """
        Devuelve las últimas N entradas del audit log.
        Usa collections.deque para leer únicamente las últimas N líneas
        sin cargar el archivo completo en memoria.
        """
        with self._lock:
            if not os.path.exists(self.log_path):
                return []

            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    tail = deque(f, maxlen=limit if limit > 0 else None)
                return [json.loads(line) for line in tail if line.strip()]
            except Exception:
                return []


# Singleton instance
audit_logger = AuditLogger()
